import pigpio  # GPIO制御
import math
import random
import socket
import json
import VL53L0X  # ToFセンサ
import threading
from rpi_ws281x import PixelStrip, Color
import time
import datetime
import sys
import spidev # 圧力センサ
import subprocess # 音声
import os

# SPIバスを開く
# 圧力
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz = 1000000

# pigpioデーモンに接続し、piオブジェクトを作成
pi = pigpio.pi()

# SG90のピン設定
SERVO_PIN = 23  # SG90
pi.set_mode(SERVO_PIN,pigpio.OUTPUT)

# ボタンのGPIO設定
BUTTON_PIN = 3
pi.set_mode(BUTTON_PIN,pigpio.INPUT)
# チャタリング対策でデバウンスを50msに
pi.set_glitch_filter(BUTTON_PIN, 50000)

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

# Create a VL53L0X object
tof = VL53L0X.VL53L0X()

# Matrix setting
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LED設定
LED_COUNT = 256  # 16x16
LED_PIN = 10
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16  # 列ごとのLED数 (16)
LED_CHANNEL = 0

MASTER_IP = "192.168.10.60"
MASTER_PORT = 5000

# スレーブの列・行番号 (マスターを0,0とする)
SLAVE_ROWS = 1  # 横方向
SLAVE_COLS = 0  # 縦方向
# スレーブ1の担当領域
SLAVE_ORIGIN_X = LED_PER_PANEL * SLAVE_ROWS  # x方向のオフセット
SLAVE_ORIGIN_Y = LED_PER_PANEL * SLAVE_COLS  # y方向のオフセット

# Matrix setup
MATRIX_GLOBAL_WIDTH = (SLAVE_ROWS + 1) * LED_PER_PANEL
MATRIX_GLOBAL_HEIGHT = (SLAVE_COLS + 1) * LED_PER_PANEL

# 円の幅
CIRCLE_WIDTH = 5

# 圧力合計の最小値
DATA_TOTAL_MIN = 1500
DATA_TOTAL_INTERVAL = 300

def quitting():
    # コールバックを解除して終了
    cb.cancel()
    pi.stop()
    # 圧力センサに関するものを閉じる
    spi.close()
    # ToFストップ
    tof.stop_ranging()
    # Clear on exit
    clear_screen()
    # server.shutdown()

    # システム終了
    print("This Raspberry Pi shutdown")
    os.system("sudo shutdown -h now")


class MasterConnection:
    def __init__(self, master_ip, master_port, row, column):
        self.master_ip = master_ip
        self.master_port = master_port
        self.row = row
        self.column = column
        self.client_socket = None
        self.client_id = self.get_client_id()
        self.connection_attempts = 0  # Counter for failed connection attempts

    def get_client_id(self):
        """ユニークなクライアントIDを生成"""
        return f"Device_{socket.gethostname()}"

    def send_to_master(self, data: dict):
        """任意のデータをマスターに送信"""
        try:
            if self.client_socket:
                self.client_socket.send(json.dumps(data).encode())
                print(f"Sent to master: {data}")
            else:
                print("Client socket is not connected.")
        except Exception as e:
            print(f"Failed to send to master: {e}")

    def listen_for_master_data(self):
        """マスターからのデータを受信"""
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                try:
                    received_data = json.loads(data.decode())
                    print(f"Received from master: {received_data}")
                    # 受信できたらデータの処理をする
                    self.handle_command(received_data)
                except json.JSONDecodeError:
                    print("Failed to decode data from master")
        except Exception as e:
            print(f"Error receiving from master: {e}")
        finally:
            self.client_socket.close()

    def handle_command(self, command):
        global isSingleMode
        # 受信したコマンドに応じて描画処理を実行する
        if command["type"] == "draw":
            x = command["x"]
            y = command["y"]
            colors = command["colors"]
            max_radius = command["max_radius"]
            animation_slave_thread = threading.Thread(target=animate_slave_circles, args=(x, y, colors, max_radius,))
            animation_slave_thread.daemon = True  # メインが終われば終わる
            animation_slave_thread.start()
        elif command["type"] == "clear":
            clear_screen()
        elif command["type"] == "multiend":
            isSingleMode = True

    def setup_slave(self):
        global isSingleMode
        """スレーブをマスターと接続（接続に失敗した場合は再接続）"""
        while self.connection_attempts < 5:  # Stop after 5 failed attempts
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.master_ip, self.master_port))
                print(f"Connected to master at {self.master_ip}:{self.master_port}")

                # 接続時に初期データを送信
                init_data = {
                    "type": "init",
                    "client_id": self.client_id,
                    "position": {"row": self.row, "column": self.column}
                }
                self.send_to_master(init_data)

                # マスターからのデータを受信するスレッドを開始
                listener_thread = threading.Thread(target=self.listen_for_master_data)
                listener_thread.daemon = True
                listener_thread.start()

                break  # 接続成功後はループを抜ける

            except (socket.error, Exception) as e:
                self.connection_attempts += 1  # Increment on failure
                print(f"Error connecting to master: {e}. Retrying in 5 seconds... Attempt {self.connection_attempts}/5")
                time.sleep(5)  # 5秒後に再試行

        if self.connection_attempts >= 5:
            print("Failed to connect after 5 attempts. Giving up.")
            # 単体機能に戻る
            isSingleMode = True




    def close_connection(self):
        """マスターとの接続を切る"""
        if self.client_socket:
            self.client_socket.close()
            print("Disconnected from master")


def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

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

def zigzag_transform(x, y, width=16):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:
        x = LED_PER_PANEL - 1 - x
    return x, y

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
            zigzag_x, zigzag_y = zigzag_transform(x, y)
            index = zigzag_y * LED_PER_PANEL + zigzag_x
            strip.setPixelColor(index, Color(0, 0, 0))

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

# スレーブの描画
def draw_slave(frame_pixels, color):
    # Draw a single frame of animation.
    slave_pixels = [p for p in frame_pixels if
                    SLAVE_ORIGIN_X <= p[0] < SLAVE_ORIGIN_X + 16 and SLAVE_ORIGIN_Y <= p[1] < SLAVE_ORIGIN_Y + 16]

    # Draw slave pixels
    for x, y in slave_pixels:
        # ローカル座標に変換
        x -= SLAVE_ORIGIN_X
        y -= SLAVE_ORIGIN_Y
        # ジグザグ変換
        zigzag_x, zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

def animate_slave_circles(xc, yc, colors, max_radius):
    radius = 0
    clear_radius = 0
    print("center of the circle: x:%d, y:%d" % (xc - SLAVE_ORIGIN_X, yc - SLAVE_ORIGIN_Y))
    # 円の描画
    while True:
        if clear_radius == max_radius:
            break
        if radius < max_radius:
            circle = circle_pixels(xc, yc, radius)
            color = colors[radius]
            
            draw_slave(circle, color)

            radius += 1

        if radius > CIRCLE_WIDTH:
            clear_circle = circle_pixels(xc, yc, clear_radius)
            # 描画を消す
            draw_slave(clear_circle, [0, 0, 0])
            clear_radius += 1
        time.sleep(0.1)

# 単体機能メイン
def single_function():
    global isSingleMode


    while True:
        # 4つの圧力センサで重さ測定
        # 圧力ループ中に複数機能に切り替えができる
        while True:
            if isSingleMode == False:
                clear_screen()
                return

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
            # data_total = 2000 # デバック用圧力合計値
            # 一定以下の圧力になったら抜ける
            # 12/17 尾崎 スレーブの音の機能
            if data_total >= DATA_TOTAL_MIN:
                if DATA_TOTAL_MIN <= data_total < DATA_TOTAL_MIN + DATA_TOTAL_INTERVAL:
                    MP3_PATH = 'music1.mp3'
                elif DATA_TOTAL_MIN + DATA_TOTAL_INTERVAL <= data_total < DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 2):
                    MP3_PATH = 'music2.mp3'
                elif DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 2) <= data_total < DATA_TOTAL_MIN + (
                        DATA_TOTAL_INTERVAL * 3):
                    MP3_PATH = 'music3.mp3'
                elif DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 3) <= data_total < DATA_TOTAL_MIN + (
                        DATA_TOTAL_INTERVAL * 4):
                    MP3_PATH = 'music4.mp3'
                elif DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 4) <= data_total:
                    MP3_PATH = 'music5.mp3'
                break
            time.sleep(0.5)
                
                
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

        # 12/17 尾崎 音再生機能
        print()
        subprocess.Popen(['mpg321',MP3_PATH])
        print()

        # Move all points toward the target simultaneously
        print("update position start")
        update_positions(points, target_x, target_y, strip, speed=0.1)
        print("update position end")

        # Clear the matrix
        clear_screen()
        

        


# 複数機能メイン
def multi_slave_function(master_connection: MasterConnection):
    global isSingleMode

    
    # スレッドでマスター接続を開始
    master_thread = threading.Thread(target=master_connection.setup_slave)
    master_thread.daemon = True
    master_thread.start()
    master_connection.setup_slave
    
    while True:
        
        # 4つの圧力センサで重さ測定
        # 圧力ループ中に複数機能に切り替えができる
        while True:
            # 単体機能に切り替わったら
            if isSingleMode == True:
                # 接続を切る
                master_connection.close_connection()
                clear_screen()
                return

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
            # data_total = 2500 # デバック用圧力合計値
            # 12/17 尾崎 音の機能実装
            # 一定以下の圧力になったら抜ける
            if data_total >= DATA_TOTAL_MIN:
                if DATA_TOTAL_MIN <= data_total < DATA_TOTAL_MIN + DATA_TOTAL_INTERVAL:
                    MP3_PATH = 'music1.mp3'
                elif DATA_TOTAL_MIN + DATA_TOTAL_INTERVAL <= data_total < DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 2):
                    MP3_PATH = 'music2.mp3'
                elif DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 2) <= data_total < DATA_TOTAL_MIN + (
                        DATA_TOTAL_INTERVAL * 3):
                    MP3_PATH = 'music3.mp3'
                elif DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 3) <= data_total < DATA_TOTAL_MIN + (
                        DATA_TOTAL_INTERVAL * 4):
                    MP3_PATH = 'music4.mp3'
                elif DATA_TOTAL_MIN + (DATA_TOTAL_INTERVAL * 4) <= data_total:
                    MP3_PATH = 'music5.mp3'
                break
            time.sleep(0.5)
                
                
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
        # target_x, target_y = MATRIX_WIDTH / 2, MATRIX_HEIGHT / 2 # デバック用
        target_x, target_y = int(target_x), int(target_y)

        # 12/17 尾崎 音再生
        print()
        subprocess.Popen(['mpg321',MP3_PATH])
        print()

        # グローバル座標に変換
        target_x += SLAVE_ORIGIN_X
        target_y += SLAVE_ORIGIN_Y
        sensor_data = {
            "type": "sensor_data",
            "x": target_x,
            "y": target_y,
            "data_total": data_total
        }
        master_connection.send_to_master(sensor_data)

        time.sleep(5) # デバッグ用

        



def button_callback(gpio, level, tick):
    global pressed_time, released_time, isSingleMode

    #print(f"Button pressed! GPIO: {gpio}, Level: {level}, Tick: {tick}")

    if level == 0:  # ボタンが押されたとき  # ボタンが押されたとき
        pressed_time = time.time()  # ボタンが押された時間を記録

    elif level == 1:
        released_time = time.time()
        press_duration = released_time - pressed_time  # 押していた時間を記録
        print(f"#####Button press duration: {press_duration:.2f} second#####")

        if press_duration >= 5:
            # 5秒以上押すとシャットダウン
            quitting()


        elif press_duration >= 0.1:
            # 複数機能に切り替え
            if isSingleMode == True:
                isSingleMode = False
                print(f"isSingleMode = {isSingleMode}\n")
            # 単体機能に切り替え
            else:
                isSingleMode = True
                print(f"isSingleMode = {isSingleMode}\n")


if __name__ == '__main__':
    # 単体機能か複数機能か判断
    isSingleMode = True
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

    pressed_time = 0
    released_time = 0

    cb = pi.callback(BUTTON_PIN, pigpio.EITHER_EDGE, button_callback)

    master_connection = MasterConnection(MASTER_IP, MASTER_PORT, SLAVE_ROWS, SLAVE_COLS)

    try:
        while True:
            # 単体機能
            if isSingleMode:
                print("-------------------------Single Mode Start-----------------------")
                single_function()
                print("-----------------------------------------------------------------\n")
            # 複数機能 (スレーブ)
            else:
                print("--------------------------Multi Mode Start-----------------------")
                multi_slave_function(master_connection)
                print("-----------------------------------------------------------------\n")
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        master_connection.close_connection()
        # コールバックを解除して終了
        cb.cancel()
        pi.stop()
        # 圧力センサに関するものを閉じる
        spi.close()
        # ToFストップ
        tof.stop_ranging()
        # Clear on exit
        clear_screen()

        # システム終了
        sys.exit(0)