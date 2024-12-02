import pigpio  # GPIO制御
from time import sleep
import datetime
import math  # 極座標変換
import VL53L0X  # ToFセンサ
import random
from rpi_ws281x import PixelStrip, Color
import sys
import spidev
import subprocess
import os
import socket
import json

# 通信関連の設定
MASTER_IP = "192.168.10.59"  # マスターのIPアドレスを実際の値に変更してください
MASTER_PORT = 5000

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

# Matrix setting
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LED Setting
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

# ソケット通信用の関数
def setup_socket():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((MASTER_IP, MASTER_PORT))
        print(f"Connected to master at {MASTER_IP}:{MASTER_PORT}")
        return client_socket
    except Exception as e:
        print(f"Failed to connect to master: {e}")
        return None

def send_sensor_data(socket, target_x, target_y, data_total):
    try:
        data = {
            "type": "sensor_data",
            "position": {
                "x": target_x,
                "y": target_y
            },
            "pressure": data_total
        }
        json_data = json.dumps(data).encode()
        socket.send(json_data)
        dt_now = datetime.datetime.now()
        print(dt_now)
        print(f"Sent data: {data}")
        
    except Exception as e:
        print(f"Error sending data: {e}")

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

        # ToFセンサで測距
        distance = tof.get_distance()
        # ToFセンサの誤差を引いて正確な値にする
        distance -= DISTANCE_ERROR
        if (distance > 0):
            # 角度と距離の表示
            print("angle: %d \t distance: %d mm" % (valInit.SvDeg, distance))
            # 極座標変換 (半径,角度)から(x,y)
            x, y = getXY(distance, valInit.SvDeg)
        sleep(timing / 1000000.00)

# 位置特定
def find_pos(timing):
    # サーボを0度に設定
    valInit.SvDeg = 0
    set_angle(valInit.SvDeg)

    sleep(0.1)

    # 配列の初期化
    pointlist = []
    flag = False
    count = 0

    for i in range(0, 91, DEGREE_CYCLE):  # 0~90度で増加量はDEGREE_CYCLE
        valInit.SvDeg = i
        set_angle(valInit.SvDeg)  # サーボを回転

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
        sleep(timing / 1000000.00)

    # 余分に記録した末尾5個のリストを削除
    del pointlist[-5:]

    # もしリストが入ってなかったら
    if len(pointlist) == 0:
        return -1, -1

    # リストの中央値(物体の中心座標)を求める
    mid = len(pointlist) // 2
    res_x = pointlist[mid][0]
    res_y = pointlist[mid][1]

    return res_x, res_y

# Led matrix
# Define zigzag matrix
def zigzag_matrix(x, y):
    if y % 2 == 0:  # Even rows
        return y * MATRIX_WIDTH + x
    else:  # Odd rows
        return y * MATRIX_HEIGHT + (MATRIX_WIDTH - 1 - x)

# Clear the matrix
def clear_matrix(strip):
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# Update positions of multiple points simultaneously
def update_positions(points, target_x, target_y, strip, speed):
    while points:
        # Update each point's position
        for point in points[:]:
            x, y, color = point
            # Clear current position
            strip.setPixelColor(zigzag_matrix(x, y), Color(0, 0, 0))

            # Calculate direction to target
            dx = target_x - x
            dy = target_y - y

            if abs(dx) < 1 and abs(dy) < 1:
                points.remove(point)
            else:
                if abs(dx) > abs(dy):
                    x += 1 if dx > 0 else -1
                else:
                    y += 1 if dy > 0 else -1
                strip.setPixelColor(zigzag_matrix(x, y), color)
                points[points.index(point)] = (x, y, color)

        strip.show()
        sleep(speed)

def main():
    valInit()  # 変数の初期化

    # ソケット接続のセットアップ
    while True:
        client_socket = setup_socket()
        if client_socket is None:
            print("Failed to setup socket connection. Exiting...")
            continue
        break

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

    cnt = 0

    try:
        while True:
            # 4つの圧力センサで重さ測定
            while True:
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
                data_total = 2500  # デバック用圧力値
                print("Data total: {0}\n".format(data_total))
                # 一定以下の圧力になったら抜ける
                if data_total <= 3600:
                    if data_total < 1800:
                        MP3_PATH = 'sample1.mp3'
                    else:
                        MP3_PATH = 'sample2.mp3'
                        break
                sleep(1)
            
            # ToFセンサとサーボで物体の位置特定
            print("find position of object:%d" % (cnt + 1))
            target_x, target_y = find_pos(timing)
            print("\n x:%d mm \t y:%d mm\n" % (target_x, target_y))

            # センサーデータの送信を追加
            send_sensor_data(client_socket, target_x, target_y, data_total)
            
            target_x /= 10 # mmからcmに変換
            target_y /= 10 # mmからcmに変換

            print(f"Target position: ({target_x}, {target_y})")

            # LEDマトリックス
            points = []
            # 圧力の値から生成する点の数を設定
            generated_points = int((10000 - data_total) / 700)
            print("generated points: %d\n" % (generated_points))
            for _ in range(generated_points):
                x = random.randint(0, MATRIX_WIDTH - 1)
                y = random.randint(0, MATRIX_HEIGHT - 1)
                color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                points.append((x, y, color))

            print("update position start")
            update_positions(points, target_x, target_y, strip, speed=0.1)
            print("update position end")

            sleep(2)
            clear_matrix(strip)

    except KeyboardInterrupt:
        if client_socket:
            client_socket.close()
        spi.close()
        tof.stop_ranging()
        clear_matrix(strip)
        sys.exit(0)

    if client_socket:
        client_socket.close()
    spi.close()
    tof.stop_ranging()
    clear_matrix(strip)
    sys.exit(0)

if __name__ == "__main__":
    main()