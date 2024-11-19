from rpi_ws281x import PixelStrip, Color
import argparse
import time
import math
import random

# パーサー設定
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--clear", action='store_true', help='clear the display on exit')
args = parser.parse_args()

# マトリクスLEDの設定
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LEDディスプレイの設定
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT  # LEDの数(16×16)
LED_PIN = 18  # GPIOピンの設定(GPIO 18)
LED_FREQ_HZ = 800000  # LED信号の周波数
LED_DMA = 10  # DMAチャンネル
LED_BRIGHTNESS = 10  # 明るさ設定(0~255)
LED_INVERT = False  # 信号の反転の有無
LED_CHANNEL = 0  # PWMチャンネル

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


def get_zigzag_index(x, y):
    """ジグザグ配線のインデックスを計算"""
    if y % 2 == 0:  # 偶数行の場合
        return y * MATRIX_WIDTH + x
    else:  # 奇数行は逆順に
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)


def set_pixel(x, y, color):
    """座標(x,y)のLEDに色を設定"""
    if 0 <= x < MATRIX_WIDTH and 0 <= y < MATRIX_HEIGHT:
        index = get_zigzag_index(x, y)
        strip.setPixelColor(index, color)


def clear_display():
    """ディスプレイをクリア"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


def draw_circle(x0, y0, radius, color):
    """円を描画"""
    x = 0
    y = radius
    d = 1 - radius

    while x <= y:
        for dx, dy in [
            (x, y), (y, x), (-x, y), (-y, x),
            (x, -y), (y, -x), (-x, -y), (-y, -x)
        ]:
            set_pixel(x0 + dx, y0 + dy, color)
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1

def main():
    print("Press Ctrl-C to quit.")
    try:
        while True:
            clear_display()

            # ランダムな位置を生成
            random_x = random.randint(0, MATRIX_WIDTH - 1)
            random_y = random.randint(0, MATRIX_HEIGHT - 1)

            # アニメーションループ
            radius = 0
            while radius < max(MATRIX_WIDTH, MATRIX_HEIGHT):
                clear_display()  # 前のフレームをクリア
                draw_circle(random_x, random_y, radius, Color(0, 255, 0))  # 緑色の円
                strip.show()
                radius += 1
                time.sleep(0.1)  # 拡大速度

            clear_display()  # 円が消えるアニメーション
            strip.show()

    except KeyboardInterrupt:
        print("\nQuitting...")
        if args.clear:
            clear_display()


if __name__ == "__main__":
    main()