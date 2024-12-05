""" スレーブ用コード """
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

""" スレーブ設定 """
# SPIバスを開く
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
# 圧力センサのチャンネルの宣言
force_channel = 0

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

""" LED設定 """
LED_COUNT = 256  # 16x16
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# マスター設定
MASTER_IP = "192.168.10.65"
MASTER_PORT = 5000

# スレーブの列・行番号 (マスターを0,0とする)
SLAVE_ROWS = 1  # 横方向
SLAVE_COLS = 1  # 縦方向
LED_PER_PANEL = 16  # 列ごとのLED数 (16)

# スレーブ1の担当領域
SLAVE_ORIGIN_X = LED_PER_PANEL * SLAVE_ROWS  # x方向のオフセット (16~)
SLAVE_ORIGIN_Y = LED_PER_PANEL * SLAVE_COLS  # y方向のオフセット (0~)

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


""" LED描画系関数 """
def zigzag_transform(x, y, width=16):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:
        x = LED_PER_PANEL - 1 - x
    return x, y


def set_pixel_local(x, y, color):
    """ローカル座標でピクセルに色を設定する。"""

    index = y * 16 + x
    strip.setPixelColor(index, Color(color[0], color[1], color[2]))


def handle_command(command):
    # 受信したコマンドに応じて描画処理を実行する
    if command["type"] == "draw":
        for global_x, global_y in command["coordinates"]:
            # このスレーブの範囲内なら
            if SLAVE_ORIGIN_X <= global_x < SLAVE_ORIGIN_X + 16 and SLAVE_ORIGIN_Y <= global_y < SLAVE_ORIGIN_Y + 16:  # 自分の範囲内
                # スレーブのオフセットを考慮してローカル座標に変換
                local_x = global_x - SLAVE_ORIGIN_X
                local_y = global_y - SLAVE_ORIGIN_Y

                # デバッグ出力: 座標変換の結果
                #print(f"グローバル座標: ({global_x}, {global_y}) → ローカル座標: ({local_x}, {local_y})")

                local_x, local_y = zigzag_transform(local_x, local_y)  # ジグザグ配列の修正
                # ジグザグ変換後の座標をデバッグ出力
                print(f"ジグザグ変換: ({local_x}, {local_y})")
                set_pixel_local(local_x, local_y, command["color"])
        strip.show()
    elif command["type"] == "clear":
        clear_screen()


def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


""" 通信関係 """
def get_client_id():
    """ユニークなクライアントIDを生成"""
    return f"Device_{socket.gethostname()}"


def listen_for_master_data(client_socket):
    """マスターからのデータを受信"""
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            try:
                received_data = json.loads(data.decode())
                print(f"Received from master: {received_data}")
                # 受信できたらデータの処理をする
                handle_command(received_data)
            except json.JSONDecodeError:
                print("Failed to decode data from master")
    except Exception as e:
        print(f"Error receiving from master: {e}")
    finally:
        client_socket.close()


def send_to_master(client_socket, data: dict):
    """任意のデータをマスターに送信"""
    try:
        client_socket.send(json.dumps(data).encode())
        print(f"Sent to master: {data}")
    except Exception as e:
        print(f"Failed to send to master: {e}")


def start_local_server(port=12345):
    #スレーブがコマンドを待機するローカルサーバー
    def server_loop():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("0.0.0.0", port))
            server_socket.listen()
            print(f"Local server listening on port {port}")
            while True:
                conn, _ = server_socket.accept()
                with conn:
                    data = b""
                    while True:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                    print(f"Received raw data: {data}")
                    try:
                        command = json.loads(data.decode('utf-8'))
                        print(f"Decoded command: {command}")
                        handle_command(command)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Raw data: {data}")

    server_thread = threading.Thread(target=server_loop, daemon=True)
    server_thread.start()


""" データ送信 """
def setup_slave(master_ip, master_port, row, column):
    """スレーブをマスターと接続"""
    client_id = get_client_id()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((master_ip, master_port))
        print(f"Connected to master at {master_ip}:{master_port}")

        # 接続時に初期データを送信
        init_data = {
            "type": "init",
            "client_id": client_id,
            "position": {"row": row, "column": column}
        }
        send_to_master(client_socket, init_data)

        # マスターからのデータを受信するスレッドを開始
        listener_thread = threading.Thread(target=listen_for_master_data, args=(client_socket,))
        listener_thread.daemon = True
        listener_thread.start()

        # 任意のデータを送信する例
        while True:
            sensor_data = {
                "type": "sensor_data",
                "client_id": client_id,
                "position": {"row": row, "column": column},
                "data": {"temperature": 25, "humidity": 60}
            }
            send_to_master(client_socket, sensor_data)
            time.sleep(5)

    except Exception as e:
        print(f"Error setting up slave: {e}")
    except KeyboardInterrupt:
        print(f"Keyboard Interrupt")
    finally:
        clear_screen()
        client_socket.close()


if __name__ == '__main__':
    clear_screen()  # 初期化で消灯
    start_local_server(port=12345)  # ローカルサーバーを開始
    setup_slave(MASTER_IP, MASTER_PORT, SLAVE_ROWS, SLAVE_COLS)  # マスターに接続
