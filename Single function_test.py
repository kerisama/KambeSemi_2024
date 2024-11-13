import random
import time
import math
#import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color

# LEDマトリクスの設定
LED_COUNT = 256  # 16x16 = 256個のLED
LED_PIN = 18     # GPIOピン
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 200 #LEDの明るさの範囲0~255
LED_INVERT = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# 圧力値をもとに円の大きさと速度を変更する関数
def pressure_to_params(pressure_value):
    # 圧力値から円の大きさを決定（圧力値が大きいほど大きな円に）
    radius = int((pressure_value / 980) * 5) + 1  # 最大半径5まで
    # 圧力値から生成速度を決定（圧力値が大きいほど速く）
    speed = max(0.01, (980 - pressure_value) / 1000)  # 圧力が高いほど速くなる
    return radius, speed

# 円を描画する関数
def draw_circle(x, y, radius, color):
    for i in range(LED_COUNT):
        col = i % 16  # x座標
        row = i // 16  # y座標
        distance = math.sqrt((x - col) ** 2 + (y - row) ** 2)
        if distance <= radius:
            strip.setPixelColor(i, color)

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

# 円を目標座標に向けて移動する関数
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
try:
    while True:
        # ランダムに円を生成
        x, y, radius, color, speed = generate_random_circle()
        draw_circle(x, y, radius, color)  # 円を表示

        # 目標座標をランダムに決定
        target_x = random.randint(0, 15)
        target_y = random.randint(0, 15)

        # 円を目標座標に移動
        move_circle(x, y, target_x, target_y, speed)

        # 少し待つ
        time.sleep(1)
finally:
    strip.show()
