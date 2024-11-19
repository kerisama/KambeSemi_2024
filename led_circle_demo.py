from rpi_ws281x import PixelStrip, Color
import argparse
import time
import math

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
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            # ピクセルと中心点との距離を計算
            distance = math.sqrt((x - x0) ** 2 + (y - y0) ** 2)
            # 半径以下の距離なら点灯
            if distance <= radius:
                set_pixel(x, y, color)


def main():
    print("Press Ctrl-C to quit.")
    try:
        while True:
            # 中心座標を設定（16x16マトリクスの中心）
            center_x = MATRIX_WIDTH / 2 - 0.5
            center_y = MATRIX_HEIGHT / 2 - 0.5

            # アニメーションループ
            for radius in range(1, 9):  # 1から8までの半径で円を描画
                clear_display()  # 前のフレームをクリア
                draw_circle(center_x, center_y, radius, Color(0, 0, 255))  # 青色の円
                strip.show()
                time.sleep(0.5)

            time.sleep(1)  # アニメーション終了後の待機時間

    except KeyboardInterrupt:
        print("\nQuitting...")
        if args.clear:
            clear_display()


if __name__ == "__main__":
    main()