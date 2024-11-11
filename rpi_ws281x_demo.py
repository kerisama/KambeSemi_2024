# ** LEDの設定 **
from rpi_ws281x import *    # rpi_ws281xのロード

# LEDマトリクスの設定
LED_COUNT = 256         # マトリクスの合計LED数 (16×16の場合)
LED_PIN = 18            # GPIOピンの設定(ここではGPIO 18)
LED_FREQ_HZ = 800000    # LED信号の周波数
LED_DMA = 10            # DMAチャンネル
LED_BRIGHTNESS = 1      # LEDの明るさ(0~255)
LED_INVERT = False      # 信号の反転(Trueの場合は信号反転)
LED_CHANNEL = 0         # PWMチャンネル

# マトリクスの大きさ
LED_MATRIX_WIDTH = 16
LED_MATRIX_HEIGHT = 16


# ** メインのプログラム **
import math
import time

# LEDストリップの初期化
strip = PixelStrip(
        LED_COUNT,
        LED_PIN,
        LED_FREQ_HZ,
        LED_DMA,
        LED_BRIGHTNESS,
        LED_INVERT,
        LED_CHANNEL
    )

# マトリクスの座標(x,y)をピクセル番号に変換する
def get_pixel_index(x,y):
    if y%2 ==0:     # 偶数行
        return y * LED_MATRIX_WIDTH + x
    else :          # 奇数行(ジグザグ配列の場合)
        return y * LED_MATRIX_HEIGHT + x

# 四角形の描画テスト
def draw_rectangle(strip,x,y,width,height,color):
    for i in range(x,x+width):
        for j in range(y,y+height):
            # LEDへの描画
            strip.setPixelColor(get_pixel_index(i,j),color)
    strip.show()

# 線の描画テスト
def draw_line(strip,x1,y1,x2,y2,color):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy   # エラー関数

    # LEDへの描画
    while True:
        strip.setPixelColor(get_pixel_index(x1,y1),color)
        if x1 == x2 and y1 == y2:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
    strip.show()

# メイン:四角形と線の描画用プログラム
try:
    # 背景の初期化
    strip.fill(Color(0,0,0))
    strip.show()

    # 四角形の描画 (左上(x,y)=(2,2)、幅と高さが4の赤い四角形)
    draw_rectangle(strip,2,2,4,4,Color(255,0,0))

    # 線の描画 (始点(x1,y1)=(0,0)、終点(x2,y2)=(15,15)の青い線)
    # ブレゼンハムのアルゴリズムで描画
    draw_line(strip,0,0,15,15,Color(0,0,255))

    # 5秒間描画する
    time.sleep(5)

    #終了時に全てのLEDを消す
    strip.fill(Color(0,0,0))
    strip.show()

# 終了処理 (プログラムを停止するとLED消灯)
except KeyboardInterrupt:
    strip.fill(Color(0,0,0))
    strip.show()
    exit(0) # 終了