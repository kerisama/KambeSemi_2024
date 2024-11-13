import time
from rpi_ws281x import *

# LEDの設定
LED_COUNT = 64          # 使用するLEDの数
LED_PIN = 18            # GPIOピンの設定 (GPIO18に接続)
LED_FREQ_HZ = 800000    # LED信号の周波数 (WS2812では800kHz)
LED_DMA = 10            # LEDのDMAチャンネル
LED_BRIGHTNESS = 50     # LEDの明るさ
LED_INVERT = False      # 信号反転
LED_CHANNEL = 0         # LEDチャンネル

# LEDの初期化(ストリップ)
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

# カラー定義
def setColor(strip,color,wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color)
        strip.show()
        time.sleep(wait_ms/1000.0)

# メインプログラム
try:
    while True:
        setColor(strip,color(255,0,0)) # 赤に点灯
        time.sleep(10)
        setColor(strip,Color(0,255,0)) # 緑に点灯
        time.sleep(10)
        setColor(strip,Color(0,0,255)) # 青に点灯
        time.sleep(10)

# 終了処理
except KeyboardInterrupt:
    setColor(strip,Color(0,0,0))   # LED消灯