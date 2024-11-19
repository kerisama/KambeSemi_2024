import time
import random
from rpi_ws281x import PixelStrip,Color
import argparse
import math

# 16x16マトリクスの設定
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LEDストリップ設定
LED_COUNT = MATRIX_HEIGHT * MATRIX_WIDTH      # LEDの総数（16x16マトリクス）
LED_PIN = 18          # GPIOピン（PWM使用）
LED_FREQ_HZ = 800000  # LED信号周波数（通常800kHz）
LED_DMA = 10          # DMAチャンネル（通常10）
LED_BRIGHTNESS = 255  # 明るさ（0-255）
LED_INVERT = False    # 信号を反転するかどうか
LED_CHANNEL = 0       # チャンネル（通常0）

# LED初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# 圧力値のしきい値 (pressure_low)
pressure_low = 980

# ジグザグ配線のインデックス計算
def get_zigzag_index(x, y):
    if y % 2 == 0:  # 偶数行はそのまま
        return y * MATRIX_WIDTH + x
    else:           # 奇数行は逆順
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

# カラーワイプ
def ColorWipe(strip,color,wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color)
        strip.show()
        time.sleep(wait_ms/1000.0)

# ランダムな圧力値を生成する関数 (デモ用)
def generate_random_pressure():
    return random.randint(10,100)

# 圧力値をもとに円の大きさと速度を変更する関数
def pressure_to_params(pressure_value):
    # 圧力値から円の大きさを決定 (圧力値が大きいほど大きくなる)
    radius = int((pressure_value/pressure_low) * 5) + 1      # 最大半径5
    # 圧力値から生成速度を決定 (圧力値が大きいと速くなる)
    speed = max(0.01,(pressure_low - pressure_value)/1000)   # 圧力が高いと速く
    return radius,speed

# 円を描画する関数
def draw_circle(x,y,radius,color):
    for i in range(LED_COUNT):
        col = i % MATRIX_HEIGHT
        row = i // MATRIX_WIDTH
        distance = math.sqrt((x - col) ** 2 + (y - row) ** 2)
        if distance <= radius:
            # ジグザグ配線の修正
            index = get_zigzag_index(col,row)
            strip.setPixelColor(index,color)
    ColorWipe(strip.color)

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

# メイン処理
def main():
    # parser設定
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--color",action='store_true',help='clear the display on exit')
    args = parser.parse_args()

    print("Press Ctrl+C to quit")

    try:
        while True:
            # ランダムに円を生成する
            x,y,radius,color,speed = generate_random_circle()
            # 円の表示
            draw_circle(x,y,radius,color)

            # 目標座標の設定
            target_x = random.randint(0,15)
            target_y = random.randint(0,15)

            # 円を目標座標に移動
            move_circle(x,y,target_x,target_y,speed)

            time.sleep(1)

    except KeyboardInterrupt:
        if args.color:
            ColorWipe(strip,Color(0,0,0),10)

if __name__ == "__main__":
    main()
