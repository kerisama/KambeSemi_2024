import time
import signal
import sys
from rpi_ws281x import PixelStrip, Color

# LEDストリップ設定
LED_COUNT = 256       # LEDの総数（16x16マトリクス）
LED_PIN = 18          # GPIOピン（PWM使用）
LED_FREQ_HZ = 800000  # LED信号周波数（通常800kHz）
LED_DMA = 10          # DMAチャンネル（通常10）
LED_BRIGHTNESS = 255  # 明るさ（0-255）
LED_INVERT = False    # 信号を反転するかどうか
LED_CHANNEL = 0       # チャンネル（通常0）

# 16x16マトリクスの設定
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# ジグザグ配線のインデックス計算
def get_pixel_index(x, y):
    if y % 2 == 0:  # 偶数行はそのまま
        return y * MATRIX_WIDTH + x
    else:           # 奇数行は逆順
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

# 三角形を描画する関数
def draw_triangle(strip, color, x0, y0, size):
    for y in range(size):
        for x in range(y + 1):  # 各行のピクセルを点灯
            index = get_pixel_index(x0 + x, y0 + y)
            if index < LED_COUNT:
                strip.setPixelColor(index, color)

# クリーンアップ処理
def clear_strip(strip):
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# メイン処理
def main():
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # SIGINT（Ctrl + C）ハンドリング
    def signal_handler(sig, frame):
        clear_strip(strip)
        print("\nプログラムを終了します。")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("三角形を描画しています。Ctrl + Cで終了します。")

    while True:
        # 三角形を描画（例：赤色、位置: (4, 4)、サイズ: 8）
        draw_triangle(strip, Color(255, 0, 0), 4, 4, 8)
        strip.show()
        time.sleep(1)

        # 三角形をクリア
        clear_strip(strip)
        time.sleep(1)

if __name__ == "__main__":
    main()
