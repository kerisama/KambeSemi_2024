import random
import time
import math
import pigpio   # GPIO制御
import VL53L0X  # Tofセンサ
from rpi_ws281x import PixelStrip, Color

# 周期ごとの度数
DEGREE_CYCLE = 1
# ディスプレイの大きさ
DISPLAY_X = 160
DISPLAY_Y = 160
# サーボの原点とディスプレイの角の点の距離(mm)
S_X = 15
S_Y = 5
# 他機体のサーボ分による範囲外識別用の座標(mm)
X_OUT = DISPLAY_X - 20
Y_OUT = DISPLAY_Y - 20
# ToFセンサの誤差(mm)
# 誤差の測定方法はVL53L0X_example.pyで定規使って計測
DISTANCE_ERROR = 30

# SG90のピン設定
SERVO_PIN = 18  # SG90

# pigpioデーモンに接続し、piオブジェクトを作成
pi = pigpio.pi()
# VL53L0Xオブジェクトの作成
tof = VL53L0X.VL53L0X()

# LEDマトリクスの設定
LED_COUNT = 256  # 16x16 = 256個のLED
LED_PIN = 18     # GPIOピン
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 200 #LEDの明るさの範囲0~255
LED_INVERT = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# ジグザグ配線の修正
def get_zigzag_index(x,y,width=16):
    if y %2 == 0:   # 偶数桁
        return y * width + x
    else:   # 奇数桁は逆順に
        return y * width + (width - 1 - x)


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

# 圧力値をもとに円の大きさと速度を変更する関数
def pressure_to_params(pressure_value):
    # 圧力値から円の大きさを決定（圧力値が大きいほど大きな円に）
    radius = int((pressure_value / 980) * 5) + 1  # 最大半径5まで
    # 圧力値から生成速度を決定（圧力値が大きいほど速く）
    speed = max(0.01, (980 - pressure_value) / 1000)  # 圧力が高いほど速くなる
    return radius, speed

# 円を描画する関数
def draw_circle(x,y,radius,color):
    for i in range(LED_COUNT):
        col = i % 16    # x座標
        row = i // 16   # y座標
        distance = math.sqrt((x - col) ** 2 + (y - row) ** 2)
        if distance <= radius:
            # ジグザグ配列のインデクス
            index = get_zigzag_index(col,row)
            strip.setPixelColor(index,color)
    strip.show()    # 変更を適用

# ランダムな圧力値を生成する関数（デモ用）
def generate_random_pressure():
    return random.randint(10, 980)

# ランダムな円を生成する関数
def generate_random_circle():
    pressure_value = generate_random_pressure()  # 圧力値を取得
    radius, speed = pressure_to_params(pressure_value)  # 圧力値から半径と速度を取得
    x = random.randint(0, 15)  # 0〜15の範囲でランダムなx座標
    y = random.randint(0, 15)  # 0〜15の範囲でランダムなy座標
    color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))  # ランダムな色
    return x, y, radius, color, speed

# 円を目標座標に向けて移動する関数　(draw_circleを更新するタイプ)
def move_circle(x, y, target_x, target_y, speed):
    step_size = 0.5  # ステップサイズ
    while x != target_x or y != target_y:
        angle = math.atan2(target_y - y, target_x - x)
        x += step_size * math.cos(angle)
        y += step_size * math.sin(angle)
        draw_circle(int(x), int(y), 2, Color(0, 0, 0))  # 以前の位置を消去
        time.sleep(speed)  # 速度調整
    draw_circle(int(x), int(y), 2, Color(0, 0, 0))  # 最終位置を消去

# メインループ
def main():
    valInit()   # 変数初期化
    #Tof起動
    tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    #
    # # 位置検出
    #
    # print("find position of object:1")
    # x, y = find_pos(timing)
    # print("\n x:%d mm \t y:%d mm\n" % (x, y))
    #
    # time.sleep(1)
    #
    # print("find position of object:2")
    # x, y = find_pos(timing)
    # print("\n x:%d mm \t y:%d mm\n" % (x, y))
    #
    # print()

    try:
        while True:
            timing = tof.get_timing()
            if (timing < 20000):
                timing = 20000
            print("Timing %d ms" % (timing / 1000))
            print()

            # 座標特定
            target_x, target_y = find_pos(timing)
            print("\n x:%d mm \t y:%d mm\n" % (x, y))
            # ランダムに円を生成
            x, y, radius, color, speed = generate_random_circle()
            draw_circle(x, y, radius, color)  # 円を表示

            # 円を目標座標に移動
            move_circle(x, y, target_x, target_y, speed)

            # 少し待つ
            time.sleep(1)

    except KeyboardInterrupt:
        # ToFストップ
        tof.stop_ranging()
        # LED消灯
        strip.fill(Color(0,0,0))
        strip.show()

if __name__ == '__main__':
    main()