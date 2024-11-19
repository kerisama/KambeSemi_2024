import time
import rpi_ws281x as ws
import signal

# LEDストリップの設定
LED_COUNT = 16 * 16  # LEDの数
LED_PIN = 18  # GPIOピン番号
LED_FREQ_HZ = 800000  # LEDストリップの周波数
LED_DMA = 10  # DMAチャンネル
LED_BRIGHTNESS = 255  # 明るさ
LED_INVERT = False  # インバート

# カラーの設定
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_WHITE = (255, 255, 255)

# LEDストリップの初期化
strip = ws.Adafruit_NeoPixel(
    LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS
)
strip.begin()

# 全てのLEDをオフにする関数
def clear_all():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, 0)
    strip.show()

# 三角形を描画する関数
def draw_triangle(color):
    clear_all()
    for i in range(16):
        for j in range(i + 1):
            index = i * 16 + j if i % 2 == 0 else i * 16 + 15 - j
            strip.setPixelColor(index, color)
    strip.show()

# Ctrl+Cで終了
def signal_handler(sig, frame):
    clear_all()
    print("Quit Sequence")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

# メインループ
while True:
    draw_triangle(COLOR_RED)
    time.sleep(1)
    draw_triangle(COLOR_GREEN)
    time.sleep(1)
    draw_triangle(COLOR_BLUE)
    time.sleep(1)