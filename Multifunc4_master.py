# Circle5_slave

import pigpio  # GPIO制御
import socket
import json
import VL53L0X  # ToFセンサ
from rpi_ws281x import PixelStrip, Color
import random
import time
import math  # 極座標変換
import threading
from typing import Dict, Tuple
import sys
import spidev # 圧力センサ
import subprocess # 音声
import os

# SPIバスを開く
# 圧力
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz = 1000000


# 周期ごとの度数
DEGREE_CYCLE = 1
# ディスプレイの大きさ(mm)
DISPLAY_X = 160
DISPLAY_Y = 160
# サーボの原点とディスプレイの角の点の距離(mm)
S_X = 15
S_Y = 5
# 他機のサーボ分による範囲外識別用の座標(mm)
X_OUT = 50
Y_OUT = DISPLAY_Y - 7
# ToFセンサの誤差(mm)
# 誤差の測定方法はVL53L0X_example.pyで定規つかって測定
DISTANCE_ERROR = 30

# SG90のピン設定
SERVO_PIN = 23  # SG90

# pigpioデーモンに接続し、piオブジェクトを作成
pi = pigpio.pi()

# Create a VL53L0X object
tof = VL53L0X.VL53L0X()

# Matrix setting
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LED configuration
LED_COUNT = 256
LED_PIN = 10
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16
LED_CHANNEL = 0

# Matrix setup
MATRIX_ROWS = 2  # 横方向
MATRIX_COLS = 1  # 縦方向
MATRIX_GLOBAL_WIDTH = MATRIX_ROWS * LED_PER_PANEL
MATRIX_GLOBAL_HEIGHT = MATRIX_COLS * LED_PER_PANEL

# 円の幅
CIRCLE_WIDTH = 5

# 通信設定
PORT = 5000


class MultiClientServer:
    def __init__(self, port: int = PORT):
        self.host = '0.0.0.0'
        self.port = port
        self.clients: Dict[Tuple[int, int], socket.socket] = {}  # {(row, column): socket}

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Master server listening on port {self.port}\n")

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
                        x = received_data["x"]
                        y = received_data["y"]
                        data_total = received_data["data_total"]
                        print("multi_animation start")
                        multi_animation(x, y, data_total)

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


# 圧力読み取りにつかう関数
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


# 位置特定につかう関数
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
    if x < X_OUT and y > Y_OUT:  # 他機のサーボ分によるディスプレイの範囲外なら
        return False
    return True

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


# LEDマトリックスに関する関数
# 奇数列の反転
def zigzag_transform(x, y):
    if y % 2 == 1:  # Zigzag for odd rows
        x = LED_PER_PANEL - 1 - x
    return x, y

# この筐体のLEDマトリックスを消灯
def clear_screen():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# 単体機能でつかう関数
# Update positions of multiple points simultaneously
# ターゲットポジションにたどり着くまで乱数で生成した位置から光をターゲットポジションに移動させる
def update_positions(points, target_x, target_y, strip, speed):
    while points:
        print("a")
        # Update each point's position
        # それぞれのポイントの座標更新
        for point in points[:]:
            x, y, color = point
            # Clear current position
            strip.setPixelColor(zigzag_matrix(x, y), Color(0, 0, 0))

            # Calculate direction to target
            dx = target_x - x
            dy = target_y - y

            #print("%d dx: %d dy: %d" % (points.index(point), dx, dy))
            # ターゲットポジションにたどり着いたら
            if abs(dx) < 1 and abs(dy) < 1:
                # ポイントの削除
                points.remove(point)
            # ターゲットポジションにたどり着いてなかったら
            else:
                # 座標更新
                if abs(dx) > abs(dy):
                    x += 1 if dx > 0 else -1
                else:
                    y += 1 if dy > 0 else -1
                zigzag_x, zigzag_y = zigzag_transform(x, y)
                index = zigzag_y * LED_PER_PANEL + zigzag_x
                # Draw new position
                strip.setPixelColor(index, color)
                # Update the point in the list
                points[points.index(point)] = (x, y, color)

        # Show updated positions
        strip.show()
        time.sleep(speed)

# 複数機能につかう関数
# 円の配列の作成
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

# マスターの描画
def draw_frame(frame_pixels, color):
    # Draw a single frame of animation.
    # この筐体の範囲内のものだけにする
    master_pixels = [p for p in frame_pixels if p[0] < LED_PER_PANEL and p[1] < LED_PER_PANEL]

    # Draw master pixels
    for x, y in master_pixels:
        zigzag_x, zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

    # print(f"Master: {master_pixels}")


# 円の描画
def animate_circles(xc, yc, colors, max_radius):
    radius = 0
    clear_radius = 0
    
    # 円の描画
    while True:
        if clear_radius == max_radius:
            break
        #print("Draw Circle :radius = %d,\t Clear Circle :radius = %d" % (radius, clear_radius))
        if radius < max_radius:
            circle = circle_pixels(xc, yc, radius)
            color = colors[radius]

            draw_frame(circle, color)
            
            radius += 1
        
        # 描画している円の幅がCIRCLE_WIDTH以上になったら真ん中から消していく
        if radius > CIRCLE_WIDTH:
            clear_circle = circle_pixels(xc,yc,clear_radius)
            # 描画を消す
            draw_frame(clear_circle,[0,0,0])
            clear_radius += 1
        time.sleep(0.1)

# x,y座標、最大半径をブロードキャスト、マスターの描画
def multi_animation(server, x, y, data_total):
    colors = []
    # 圧力値をもとに最大半径を決める
    max_radius = int((4000 - data_total) / 100)

    # 最大半径の最小値はCIRCLE_WIDTH + 1
    if max_radius <= CIRCLE_WIDTH:
        max_radius = CIRCLE_WIDTH + 1
            
    #x, y = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
    #x, y = random.randint(0, MATRIX_GLOBAL_WIDTH - 1), random.randint(0, MATRIX_GLOBAL_HEIGHT - 1)
    print("x:%d, y:%d. max_radius:%d" % (x, y, max_radius))

    for i in range(max_radius):
        color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
        colors.append(color)

    # スレーブに送信
    command = {"type": "draw", "x": x, "y": y, "colors": colors, "max_radius": max_radius}
    server.broadcast(command)

    # 円描画のスレッドを作成 argsはanimate_circlesの引数 x,y 受け取ったら
    animation_thread = threading.Thread(target=animate_circles, args=(x,y,colors,max_radius,))
    animation_thread.daemon = True # メインが終われば終わる
    animation_thread.start()


# 単体機能メイン
def single_function():
    try:
        while True:
            # 4つの圧力センサで重さ測定
            # 圧力ループ中に複数機能に切り替えができる
            while True:
                """
                # 複数機能ボタンおされたらreturn False
                """
                # 圧力の合計データの初期化
                data_total = 0
                # ４箇所の圧力を測定
                for i in range(4):
                    # センサのチャンネルの切り替え
                    data = ReadChannel(i)
                    data_total += data
                    print("channel: %d" % (i))
                    print("A/D Converter: {0}".format(data))
                    volts = ConvertVolts(data,3)
                    print("Volts: {0}".format(volts))
                # ４つの圧力の合計値(通信する変数1:data_total)
                print("Data total: {0}\n".format(data_total))
                data_total = 2000 # デバック用圧力合計値
                # 一定以下の圧力になったら抜ける
                if data_total <= 3600:
                    if data_total < 1800:
                        MP3_PATH = 'sample1.mp3'
                    else:
                        MP3_PATH = 'sample2.mp3'
                        break
                    
                    
            """
            #os.system("amixer sset Master on")
            print()
            # 音を鳴らす
            #subprocess.Popen(['aplay', 'test.wav'])
            time.sleep(3)
            args =  ['kill', str(process.pid)]
            subprocess.Popen(args)
            #os.system("amixer sset Master off")
            print()
            """
                    
            # ToFセンサとサーボで物体の位置特定
            print("find position of object")
            target_x, target_y = find_pos(timing)
            print("\n x:%d mm \t y:%d mm\n" % (target_x, target_y))
            # 物体の座標x,y(通信で使う変数2,3:target_x, target_y)
            target_x /= 10 # mmからcmに変換
            target_y /= 10 # mmからcmに変換

            print(f"Target position: ({target_x}, {target_y})")
            # target_x, target_y = MATRIX_WIDTH / 2, MATRIX_HEIGHT / 2

            # LEDマトリックス
            # Generate multiple random starting points and their colors
            points = []
            # 圧力の値から生成する点の数を設定
            generated_points = int((10000 - data_total) / 700)
            print("generated points: %d\n" % (generated_points))
            for _ in range(generated_points):  # Number of points
                x = random.randint(0, MATRIX_WIDTH - 1)
                y = random.randint(0, MATRIX_HEIGHT - 1)
                color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                points.append((x, y, color))

            # Move all points toward the target simultaneously
            print("update position start")
            update_positions(points, target_x, target_y, strip, speed=0.1)
            print("update position end")

            # Clear the matrix
            clear_matrix(strip)
        
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        # 圧力センサに関するものを閉じる
        spi.close()
        # ToFストップ
        tof.stop_ranging()
        # Clear on exit
        clear_matrix(strip)
        # システム終了
        sys.exit(0)


# 複数機能メイン
def multi_function():
    # サーバーのスレッドを立ち上げてサーバーをつくる
    server = MultiClientServer()
    server_thread = threading.Thread(target=server.start_server)
    server_thread.daemon = True # メインが終われば終わる
    server_thread.start()
    
    try:
        while True:
            
            # 4つの圧力センサで重さ測定
            # 圧力ループ中に複数機能に切り替えができる
            while True:
                """
                # 複数機能ボタンおされたらreturn True
                if ~~~:
                    clear_screen()
                    command = {"type": "isSingle"}
                    server.broadcast(command)
                    if hasattr(server, 'server_socket'):
                        print("Server shutdown")
                        server.shutdown(server.server_socket)
                    else:
                        print("Server socket not found.")
                    return True
                """
                # 圧力の合計データの初期化
                data_total = 0
                # ４箇所の圧力を測定
                for i in range(4):
                    # センサのチャンネルの切り替え
                    data = ReadChannel(i)
                    data_total += data
                    print("channel: %d" % (i))
                    print("A/D Converter: {0}".format(data))
                    volts = ConvertVolts(data,3)
                    print("Volts: {0}".format(volts))
                # ４つの圧力の合計値(通信する変数1:data_total)
                print("Data total: {0}\n".format(data_total))
                data_total = 2500 # デバック用圧力合計値
                # 一定以下の圧力になったら抜ける
                if data_total <= 3600:
                    if data_total < 1800:
                        MP3_PATH = 'sample1.mp3'
                    else:
                        MP3_PATH = 'sample2.mp3'
                        break
                    
                    
            """
            #os.system("amixer sset Master on")
            print()
            # 音を鳴らす
            #subprocess.Popen(['aplay', 'test.wav'])
            time.sleep(3)
            args =  ['kill', str(process.pid)]
            subprocess.Popen(args)
            #os.system("amixer sset Master off")
            print()
            """
                    
            # ToFセンサとサーボで物体の位置特定
            print("find position of object")
            target_x, target_y = find_pos(timing)
            #print("\n x:%d mm \t y:%d mm\n" % (target_x, target_y))
            # 物体の座標x,y(通信で使う変数2,3:target_x, target_y)
            target_x /= 10 # mmからcmに変換
            target_y /= 10 # mmからcmに変換

            print(f"Target position: ({target_x}, {target_y})")
            target_x, target_y = MATRIX_WIDTH / 2, MATRIX_HEIGHT / 2 # デバック用
            target_x, target_y = int(target_x), int(target_y)
            multi_animation(server, target_x, target_y, data_total)
            time.sleep(5)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        
        # 圧力センサに関するものを閉じる
        spi.close()
        # ToFストップ
        tof.stop_ranging()
        # 終了 (円の削除)
        clear_screen()
        command = {"type": "clear"}
        server.broadcast(command)
        if hasattr(server, 'server_socket'):
            print("Server shutdown")
            server.shutdown(server.server_socket)
        else:
            print("Server socket not found.")
        # システム終了
        sys.exit(0)
            

if __name__ == '__main__':
    # 初期設定
    valInit()  # 変数の初期化

    # ToF起動
    tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    timing = tof.get_timing()
    if (timing < 20000):
        timing = 20000
    print("Timing %d ms" % (timing / 1000))

    print()

    # LED setting
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    # 初期設定終了
    
    clear_screen()
    
    # 単体機能か複数機能か判断
    isSingleMode = False

    while True:
        if isSingleMode:
            isSingleMode = single_function()
        else:
            isSingleMode = multi_function()

        
    
    # 複数機能になるごとにさーばーたてる、単体になったらサーバーとじるでいけるかも
    # スレーブはせつぞくがきれたら単体機能にもどる？
    
    
    
    
    
