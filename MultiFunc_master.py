import random
from typing import Dict, Tuple
import socket
import json
import threading
from rpi_ws281x import PixelStrip, Color
import time
import pigpio
import VL53L0X
import math
import sys
import spidev
import subprocess
import os

from sympy.codegen.ast import continue_

""" 圧力センサ設定 """
# SPIバスを開く
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
# 圧力センサのチャンネルの宣言
force_channel = 0

""" サーボモータとToFセンサの設定 """
# 周期ごとの度数
DEGREE_CYCLE = 1
# ディスプレイの大きさ(mm)
DISPLAY_X = 160
DISPLAY_Y = 160
# サーボの原点とディスプレイの角の点の距離(mm)
S_X = 15
S_Y = 5
# 他機のサーボ分による範囲外識別用の座標(mm)
X_OUT = DISPLAY_X - 20
Y_OUT = DISPLAY_Y - 20
# ToFセンサの誤差(mm)
# 誤差の測定方法はVL53L0X_example.pyで定規つかって測定
DISTANCE_ERROR = 30

# SG90のピン設定
SERVO_PIN = 23  # SG90

# pigpioデーモンに接続し、piオブジェクトを作成
pi = pigpio.pi()

# Create a VL53L0X object
tof = VL53L0X.VL53L0X()

# LED configuration
LED_COUNT = 256
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16

# Matrix setup
MATRIX_WIDTH = 2  # Number of horizontal panels
MATRIX_HEIGHT = 2  # Number of vertical panels
MATRIX_GLOBAL_WIDTH = MATRIX_WIDTH * LED_PER_PANEL
MATRIX_GLOBAL_HEIGHT = MATRIX_HEIGHT * LED_PER_PANEL

# 通信設定
PORT = 5000

# Initialize master LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()


class MultiClientServer:
    def __init__(self, port: int = 5000):
        self.host = '0.0.0.0'
        self.port = port
        self.clients: Dict[Tuple[int, int], socket.socket] = {}  # {(row, column): socket}

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Master server listening on port {self.port}")

        try:
            while True:
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.shutdown(server_socket)

    def handle_client(self, client_socket: socket.socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                try:
                    received_data = json.loads(data.decode())
                    if received_data["type"] == "init":
                        # クライアントの位置情報を登録
                        position = tuple(received_data["position"].values())  # (row, column)
                        self.clients[position] = client_socket
                        print(f"Registered client at position: {position}")

                    elif received_data["type"] == "sensor_data":
                        position = tuple(received_data["position"].values())
                        print(f"Received from {position}: {received_data}")

                except json.JSONDecodeError:
                    print("Failed to decode data from client")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.remove_client(client_socket)

    def send_to_position(self, row: int, column: int, data: dict):
        """特定の位置にデータを送信"""
        position = (row, column)
        if position in self.clients:
            try:
                self.clients[position].send(json.dumps(data).encode())
                print(f"Sent to {position}: {data}")
            except Exception as e:
                print(f"Failed to send to {position}: {e}")
        else:
            print(f"No client at position {position}")

    def broadcast(self, data: dict):
        """すべてのクライアントにデータをブロードキャスト"""
        for position, client_socket in list(self.clients.items()):
            try:
                client_socket.send(json.dumps(data).encode())
                print(f"Broadcasted to {position}: {data}")
            except Exception as e:
                print(f"Failed to broadcast to {position}: {e}")

    def remove_client(self, client_socket: socket.socket):
        """クライアントを削除"""
        for position, socket in list(self.clients.items()):
            if socket == client_socket:
                del self.clients[position]
                print(f"Removed client at position: {position}")
                break

    def shutdown(self, server_socket):
        """すべてのクライアントとサーバーソケットを閉じる"""
        for client_socket in self.clients.values():
            client_socket.close()
        server_socket.close()
        print("Server shutdown complete")


def zigzag_transform(x, y):
    if y % 2 == 1:  # Zigzag for odd rows
        x = LED_PER_PANEL - 1 - x
    return x, y


def clear_screen():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


def circle_pixels(xc, yc, radius):
    """Generate circle pixels for a given center and radius."""
    x, y = 0, radius
    d = 1 - radius
    pixels = []

    while x <= y:

        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < MATRIX_GLOBAL_WIDTH and 0 <= yc + dy < MATRIX_GLOBAL_HEIGHT:
                pixels.append((xc + dx, yc + dy))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return pixels


def draw_frame(frame_pixels, color, collision_pixels=None, mix_color=None):
    # アニメーション描画
    # マスターの範囲内ならmaster_pixelsに、それ以外はslave_pixelsにする
    master_pixels = [p for p in frame_pixels if p[0] < LED_PER_PANEL and p[1] < LED_PER_PANEL]
    slave_pixels = [p for p in frame_pixels if p[0] >= LED_PER_PANEL or p[1] >= LED_PER_PANEL]

    # Draw master pixels
    for x, y in master_pixels:
        zigzag_x, zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x

        # 円がぶつかったところの描画
        if collision_pixels and (x, y) in collision_pixels:
            # 混ざった色を描画する
            strip.setPixelColor(index,Color(mix_color[0], mix_color[1], mix_color[2]))
        else:   # ぶつかっていないところの描画
            strip.setPixelColor(index,Color(color[0],color[1],color[2]))

    strip.show()

    # print(f"Master: {master_pixels}")
    print(f"Slave: {slave_pixels}")

    return slave_pixels, color


def animate_circles(server):
    max_radius = min(MATRIX_GLOBAL_WIDTH, MATRIX_GLOBAL_HEIGHT) // 2
    # max_radius = 15

    # マスターのセンサデータを取得
    timing = tof.get_timing()
    if timing < 20000:
        timing = 20000
    master_x, master_y = find_pos(timing)  # マスターの位置を検出
    # master_x, master_y = 5,5
    print(f"master target: (x,y) = ({master_x}, {master_y})")

    slave_data = []
    for position, client_socket in server.clients.items():
        try:
            # データをリクエスト
            request_data = {"type": "request_data"}
            client_socket.send(json.dumps(request_data).encode())
            data = client_socket.recv(1024)
            if data:
                received_data = json.loads(data.decode())
                if received_data["type"] == "sensor_data":
                    slave_data.append(received_data)
                    print("received data from slaves!")
        except Exception as e:
            print(f"Error communicating with slave {position}: {e}")

    # スレーブデータを近い順にソート
    slave_data.sort(key=lambda d: d["data"]["x"] ** 2 + d["data"]["y"] ** 2)

    # マスターが物体を検知した場合
    if master_x != -1 and master_y != -1:
        circle1_data = {"data": {"x": master_x, "y": master_y}}
        if len(slave_data) > 0:
            circle2_data = slave_data[0]
        else:
            circle2_data = {"data": {"x": master_x + 10, "y": master_y + 10}}  # 仮想データ
    elif len(slave_data) >= 2:
        # スレーブデータのみで描画
        circle1_data = slave_data[0]
        circle2_data = slave_data[-1]
    elif len(slave_data) == 1:
        # スレーブデータが1つしかない場合
        circle1_data = slave_data[0]
        # 仮データで描画
        circle2_data = {"data": {"x": random.randint(1,MATRIX_GLOBAL_WIDTH), "y": random.randint(1,MATRIX_GLOBAL_HEIGHT)}}
    else:
        # データがない場合
        print("No data available to animate circles.")
        return  # 何も描画せずに終了

    # 座標を抽出
    xc1, yc1 = int(circle1_data["data"]["x"]), int(circle1_data["data"]["y"])
    xc2, yc2 = int(circle2_data["data"]["x"]), int(circle2_data["data"]["y"])
    print(f"circle1: (x,y) = ({xc1}, {yc1})")
    print(f"circle2: (x,y) = ({xc2}, {yc2})")

    # ランダムな色を生成
    color1 = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
    color2 = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

    # 円のアニメーション
    for radius in range(max_radius):
        circle1 = circle_pixels(xc1, yc1, radius)
        circle2 = circle_pixels(xc2, yc2, radius)

        # 衝突処理
        collision = set(circle1) & set(circle2)
        if collision:
            print("Collision detected!")
        mix_color = [
            (color1[0] + color2[0]) // 2,
            (color1[1] + color2[1]) // 2,
            (color1[2] + color2[2]) // 2
        ] if collision else None

        slave_pixels1, color1 = draw_frame(circle1, color1, collision, mix_color)
        slave_pixels2, color2 = draw_frame(circle2, color2, collision, mix_color)

        # スレーブに描画指令を送信
        if len(slave_pixels1):
            command = {"type": "draw", "coordinates": slave_pixels1, "color": color1}
            server.broadcast(command)
        if len(slave_pixels2):
            command = {"type": "draw", "coordinates": slave_pixels2, "color": color2}
            server.broadcast(command)
        time.sleep(0.1)


    """
    # 円の中心を指定
    xc1, yc1 = 15, 1    # スレーブからのセンサの値を取得したもの
    xc2, yc2 = 18, 1    # スレーブからのセンサの値を取得したもの

    # 色の指定
    color1 = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
    color2 = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

    # 円の描画
    for radius in range(max_radius):
        circle1 = circle_pixels(xc1, yc1, radius)
        circle2 = circle_pixels(xc2, yc2, radius)

        # 衝突処理
        collision = set(circle1) & set(circle2)
        mix_color = [
            (color1[0] + color2[0]) // 2,
            (color1[1] + color2[1]) // 2,
            (color1[2] + color2[2]) // 2
        ] if collision else None

        slave_pixels1, color1 = draw_frame(circle1, color1,collision, mix_color)
        slave_pixels2, color2 = draw_frame(circle2, color2,collision, mix_color)
        # スレーブに送信
        # slave_pixelsがあれば全スレーブに送信(broadcast)
        if len(slave_pixels1):  # 円1の描画
            command = {"type": "draw", "coordinates": slave_pixels1, "color": color1}
            server.broadcast(command)
        if len(slave_pixels2):  # 円2の描画
            command = {"type": "draw", "coordinates": slave_pixels2, "color": color2}
            server.broadcast(command)
        time.sleep(0.1)
    """

    # 消す
    for radius in range(max_radius):
        circle1 = circle_pixels(xc1,yc1,radius)
        circle2 = circle_pixels(xc2,yc2,radius)
        slave_pixels1, color1 = draw_frame(circle1,Color(0,0,0))
        slave_pixels2, color2 = draw_frame(circle2,Color(0,0,0))
        if len(slave_pixels1):  # 円1の削除
            command = {"type": "draw", "coordinates": slave_pixels1, "color": color1}
            server.broadcast(command)
        if len(slave_pixels2):  # 円2の削除
            command = {"type": "draw", "coordinates": slave_pixels2, "color": color2}
            server.broadcast(command)
        time.sleep(0.1)

    return server


""" センサ系関数 """
# MCP3008から値を読み取るメソッド
# チャンネル番号は0から7まで
def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


# 得た値を電圧に変換するメソッド
# 指定した桁数で切り捨てる
def ConvertVolts(data, places):
    volts = (data * 5) / float(1023)
    volts = round(volts, places)
    return volts


# 変数の初期化
def valInit():
    valInit.SvDeg = 0  # サーボモータの現在角度


# サーボモータを特定の角度に設定する関数
def set_angle(angle):
    assert 0 <= angle <= 180, '角度は0から180の間でなければなりません'

    # 角度を500(半時計まわり最大90度)から2500(時計まわり最大90度)のパルス幅にマッピング
    pulse_width = (angle / 180) * (2500 - 500) + 500

    # パルス幅を設定してサーボを回転
    pi.set_servo_pulsewidth(SERVO_PIN, pulse_width)


# 極座標変換
def getXY(r, degree):
    rad = math.radians(degree)
    x = r * math.cos(rad)
    y = r * math.sin(rad)
    # print(x, y)
    return x, y


def calculateGap(degree):
    rad = math.radians(degree)
    X_GAP = S_X - S_X * math.sin(rad)
    Y_GAP = -S_Y + S_X * math.cos(rad)
    return X_GAP, Y_GAP


# 範囲内か識別
def isRange(x, y):
    if x > DISPLAY_X or y > DISPLAY_Y:  # ディスプレイの大きさ外なら
        return False
    if x > X_OUT and y > Y_OUT:  # 他機のサーボ分によるディスプレイの範囲外なら
        return False
    return True


# サーボとToFセンサのテスト関数
def servo_tof_test(timing):
    # サーボを0度に設定
    valInit.SvDeg = 0
    set_angle(valInit.SvDeg)

    for i in range(0, 90, DEGREE_CYCLE):  # 0~90度で増加量はDEGREE_CYCLE
        valInit.SvDeg = i
        set_angle(valInit.SvDeg)  # サーボを回転
        # print(valInit.SvDeg)

        # ToFセンサで測距
        distance = tof.get_distance()
        # ToFセンサの誤差を引いて正確な値にする
        distance -= DISTANCE_ERROR
        if (distance > 0):
            # 角度と距離の表示
            print("angle: %d \t distance: %d mm" % (valInit.SvDeg, distance))
            # 極座標変換 (半径,角度)から(x,y)
            x, y = getXY(distance, valInit.SvDeg)
        time.sleep(timing / 1000000.00)


# 位置特定
def find_pos(timing):
    # 極座標の特定(角度, 距離)
    # 極座標変換(x, y)および範囲内かどうか
    # 範囲内の最初と最後のx,yを配列に入れる
    # 配列から範囲内に最初になった座標と最後に範囲内になった座標の中心(物体の中心座標)を返す

    # サーボを0度に設定
    valInit.SvDeg = 0
    set_angle(valInit.SvDeg)

    time.sleep(0.1)

    # 配列の初期化
    pointlist = []

    flag = False

    count = 0

    for i in range(0, 91, DEGREE_CYCLE):  # 0~90度で増加量はDEGREE_CYCLE
        valInit.SvDeg = i
        set_angle(valInit.SvDeg)  # サーボを回転
        # print(valInit.SvDeg)

        # ToFセンサで測距
        distance = tof.get_distance()
        # ToFセンサの誤差を引いて正確な値にする
        distance -= DISTANCE_ERROR
        if (distance > 0):
            # 角度と距離の表示
            print("angle: %d \t distance: %d mm" % (valInit.SvDeg, distance))

            # 極座標変換 (半径,角度)から(x,y)
            x, y = getXY(distance, valInit.SvDeg)
            X_GAP, Y_GAP = calculateGap(valInit.SvDeg)
            x -= X_GAP  # x座標のずれを減らす
            y -= Y_GAP  # y座標のずれを減らす
            print("pos:x %d, y %d \t GAP:x %d, y %d" % (x, y, X_GAP, Y_GAP))
            if not flag:  # flagがFalseのとき
                if isRange(x, y):  # 範囲内なら
                    print("isrange true")
                    count += 1
                else:
                    print("isrange false")
                    count = 0
                if count == 5:  # 5度連続で範囲内ならflagをtrueに
                    flag = True
            else:  # flagがTrueのとき
                pointlist.append([x, y])
                print(pointlist[-1])
                if not isRange(x, y):  # 範囲外なら
                    print("isrange false")
                    count += 1
                else:
                    print("isrange true")
                    count = 0
                if count == 5:  # 5度連続で範囲外ならforをぬける
                    break
        time.sleep(timing / 1000000.00)

    # 余分に記録した末尾5個のリストを削除
    del pointlist[-5:]
    # print(pointlist)

    # もしリストが入ってなかったら
    if len(pointlist) == 0:
        return -1, -1

    # リストの中央値(物体の中心座標)を求める
    mid = len(pointlist) // 2
    res_x = pointlist[mid][0]
    res_y = pointlist[mid][1]

    return res_x, res_y


if __name__ == '__main__':
    # 通信設定
    clear_screen()
    server = MultiClientServer()
    server_thread = threading.Thread(target=server.start_server)
    server_thread.daemon = True
    server_thread.start()
    try:
        while True:
            # 円のアニメーション
            animate_circles(server)
    except KeyboardInterrupt:
        # 終了 (円の削除)
        clear_screen()
        command = {"type": "clear"}
        server.broadcast(command)
    finally:
        if hasattr(server, 'server_socket'):
            server.shutdown(server.server_socket)
        else:
            print("Server socket not found.")
