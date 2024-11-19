# ライブラリのロード (rpi-ws281x-pythonライブラリをインストールする必要がある)
from rpi_ws281x import PixelStrip,Color
import argparse
import time
import math

# マトリクスLEDの設定
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LEDディスプレイの設定
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT         #LEDの数(16×16)
LED_PIN = 18            #GPIOピンの設定(ここではGPIO 18)
LED_FREQ_HZ = 800000    #LED信号の周波数
LED_DMA = 10            #DMAチャンネル
LED_BRIGHTNESS = 10     #明るさ設定(0~255)
LED_INVERT = False      #信号の反転の有無
LED_CHANNEL = 0         #PWMチャンネル

# マトリクスオブジェクトの作成
strip = PixelStrip(
        LED_COUNT,
        LED_PIN,
        LED_FREQ_HZ,
        LED_DMA,
        LED_BRIGHTNESS,
        LED_INVERT,
        LED_CHANNEL
    )
strip.begin()

# LEd表示
def get_zigzag_index(x,y):
    if y % 2 == 0:      # 偶数行の場合
        return y * MATRIX_WIDTH + x
    else:               # 奇数桁は逆順に
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

# カラーワイプ
def ColorWipe(strip,color,wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

# 円の描画(一定時間ごとに広がる)
def draw_circle(x0, y0, radius, color):
    for y in range(8):
        for x in range(8):
            if math.sqrt((x - x0) ** 2 + (y - y0) ** 2) <= radius:
                ColorWipe(x, y, color)

# parser設定
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--color",action='store_true',help='clear the display on exit')
    args = parser.parse_args()

# 円の描画(一定時間ごとに広がる)
try:
    while True:
        strip.clear()
        for radius in range(1, 6):  # 1から5までの半径で円を描画
            # 中心から円が広がっていく
            draw_circle(3.5, 3.5, radius, Color(0, 0, 255))  # 青色の円
            strip.show()
            time.sleep(0.5)
        time.sleep(1)  # アニメーション終了後の待機時間

# 終了処理
except KeyboardInterrupt:
    if args.color:
        ColorWipe(strip,Color(0,0,0),10)