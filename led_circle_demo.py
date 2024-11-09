# ライブラリのロード (rpi-ws281x-pythonライブラリをインストールする必要がある)
from rpi_ws281x import *
import time
import math

# LEDディスプレイの設定
LED_COUNT = 256         #LEDの数(16×16)
LED_PIN = 18            #GPIOピンの設定(ここではGPIO 18)
LED_FREQ_HZ = 800000    #LED信号の周波数
LED_DMA = 10            #DMAチャンネル
LED_BRIGHTNESS = 10     #明るさ設定(0~255)
LED_INVERT = False      #信号の反転の有無
LED_CHANNEL = 0         #PWMチャンネル

# マトリクスオブジェクトの作成
matrix = Adafruit_NeoPixel(
        LED_COUNT,
        LED_PIN,
        LED_FREQ_HZ,
        LED_DMA,
        LED_BRIGHTNESS,
        LED_INVERT,
        LED_CHANNEL
    )
matrix.begin()

# LEd表示
def set_pixel(x, y, color):
    index = y * 8 + x
    matrix.setPixelColor(index, color)

# LEDのリセット
def clear_matrix():
    for i in range(LED_COUNT):
        matrix.setPixelColor(i, Color(0, 0, 0))
    matrix.show()

# 円の描画(一定時間ごとに広がる)
def draw_circle(x0, y0, radius, color):
    for y in range(8):
        for x in range(8):
            if math.sqrt((x - x0) ** 2 + (y - y0) ** 2) <= radius:
                set_pixel(x, y, color)

# 円の描画(一定時間ごとに広がる)
try:
    while True:
        for radius in range(1, 6):  # 1から5までの半径で円を描画
            clear_matrix()
            draw_circle(3.5, 3.5, radius, Color(0, 0, 255))  # 青色の円
            matrix.show()
            time.sleep(0.5)
        time.sleep(1)  # アニメーション終了後の待機時間

# 終了処理
except KeyboardInterrupt:
    clear_matrix()