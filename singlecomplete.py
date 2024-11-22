import pigpio   # GPIO制御
from time import sleep
import math     # 極座標変換
import VL53L0X  # ToFセンサ
import random
from rpi_ws281x import PixelStrip, Color

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
SERVO_PIN = 18  # SG90

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
    #print(x, y)
    return x, y

def calculateGap(degree):
    rad = math.radians(degree)
    X_GAP = S_X - S_X * math.sin(rad)
    Y_GAP = -S_Y + S_X * math.cos(rad)
    return X_GAP, Y_GAP

# 範囲内か識別
def isRange(x, y):
    if x > DISPLAY_X or y > DISPLAY_Y: # ディスプレイの大きさ外なら
        return False
    if x > X_OUT and y > Y_OUT: # 他機のサーボ分によるディスプレイの範囲外なら
        return False
    return True

# サーボとToFセンサのテスト関数
def servo_tof_test(timing):
    # サーボを0度に設定
    valInit.SvDeg = 0
    set_angle(valInit.SvDeg)
    
    for i in range(0, 90, DEGREE_CYCLE): # 0~90度で増加量はDEGREE_CYCLE
        valInit.SvDeg = i
        set_angle(valInit.SvDeg) # サーボを回転
        #print(valInit.SvDeg)
        
        # ToFセンサで測距
        distance = tof.get_distance()
        # ToFセンサの誤差を引いて正確な値にする
        distance -= DISTANCE_ERROR
        if(distance > 0):
            # 角度と距離の表示
            print("angle: %d \t distance: %d mm" % (valInit.SvDeg, distance))
            # 極座標変換 (半径,角度)から(x,y)
            x, y = getXY(distance, valInit.SvDeg)
        sleep(timing/1000000.00)

# 位置特定
def find_pos(timing):
    # 極座標の特定(角度, 距離)
    # 極座標変換(x, y)および範囲内かどうか
    # 範囲内の最初と最後のx,yを配列に入れる
    # 配列から範囲内に最初になった座標と最後に範囲内になった座標の中心(物体の中心座標)を返す
    
    # サーボを0度に設定
    valInit.SvDeg = 0
    set_angle(valInit.SvDeg)
    
    sleep(0.1)
    
    # 配列の初期化
    pointlist = []
    
    flag = False
    
    count = 0
    
    for i in range(0, 91, DEGREE_CYCLE): # 0~90度で増加量はDEGREE_CYCLE
        valInit.SvDeg = i
        set_angle(valInit.SvDeg) # サーボを回転
        #print(valInit.SvDeg)

        # ToFセンサで測距
        distance = tof.get_distance()
        # ToFセンサの誤差を引いて正確な値にする
        distance -= DISTANCE_ERROR
        if(distance > 0):
            # 角度と距離の表示
            print("angle: %d \t distance: %d mm" % (valInit.SvDeg, distance))

            # 極座標変換 (半径,角度)から(x,y)
            x, y = getXY(distance, valInit.SvDeg)
            X_GAP, Y_GAP = calculateGap(valInit.SvDeg)            
            x -= X_GAP # x座標のずれを減らす
            y -= Y_GAP # y座標のずれを減らす
            print("pos:x %d, y %d \t GAP:x %d, y %d" % (x, y, X_GAP, Y_GAP))
            if not flag: # flagがFalseのとき
                if isRange(x, y): # 範囲内なら
                    print("isrange true")
                    count += 1
                else:
                    print("isrange false")
                    count = 0
                if count == 5:  # 5度連続で範囲内ならflagをtrueに
                    flag = True
            else:   # flagがTrueのとき
                pointlist.append([x, y])
                print(pointlist[-1])
                if not isRange(x, y): # 範囲外なら
                    print("isrange false")
                    count += 1
                else:
                    print("isrange true")
                    count = 0
                if count == 5:  # 5度連続で範囲外ならforをぬける
                    break
        sleep(timing/1000000.00)
        
    # 余分に記録した末尾5個のリストを削除
    del pointlist[-5:]
    #print(pointlist)
    
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
def update_positions(points, target_x, target_y, strip, speed=0.05):
    while points:
        # Update each point's position
        for point in points[:]:
            x, y, color = point
            # Clear current position
            strip.setPixelColor(zigzag_matrix(x, y), Color(0, 0, 0))

            # Calculate direction to target
            dx = target_x - x
            dy = target_y - y
            if dx == 0 and dy == 0:
                # Point has reached the target
                points.remove(point)
                continue
            elif abs(dx) > abs(dy):
                x += 1 if dx > 0 else -1
            else:
                y += 1 if dy > 0 else -1

            # Draw new position
            strip.setPixelColor(zigzag_matrix(x, y), color)
            # Update the point in the list
            points[points.index(point)] = (x, y, color)

        # Show updated positions
        strip.show()
        sleep(speed)


def main():
    valInit() # 変数の初期化
    
    # ToF起動
    tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    timing = tof.get_timing()
    if (timing < 20000):
        timing = 20000
    print ("Timing %d ms" % (timing/1000))
    
    print()
    
    # 位置検出
    
    print("find position of object:1")
    target_x, target_y = find_pos(timing)
    print("\n x:%d mm \t y:%d mm\n" % (target_x, target_y))
    target_x /= 10
    target_y /= 10
    
    sleep(1)
    
    # ToFストップ
    tof.stop_ranging()
    
    # LED setting
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    try:
        while True:
            # Generate multiple random starting points and their colors
            points = []
            for _ in range(10):  # Number of points
                x = random.randint(0, MATRIX_WIDTH - 1)
                y = random.randint(0, MATRIX_HEIGHT - 1)
                color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                points.append((x, y, color))


            print(f"Target position: ({target_x}, {target_y})")

            # Move all points toward the target simultaneously
            update_positions(points, target_x, target_y, strip, speed=0.05)

            # Pause before resetting
            sleep(2)

            # Clear the matrix
            clear_matrix(strip)

    except KeyboardInterrupt:
        # Clear on exit
        clear_matrix(strip)

    return

if __name__ == "__main__":
    main()
