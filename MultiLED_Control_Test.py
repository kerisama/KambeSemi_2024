import time
from rpi_ws281x import PixelStrip,Color
import argparse
import math

# マトリクスの設定
MATRIX_WIDTH = 16   # 横の長さ
MATRIX_HEIGHT = 16  # 縦の長さ

# マトリクスLEDの数
MATRIX_ROWS = 1     # 横方向のマトリクス数
MATRIX_COLS = 1     # 縦方向のマトリクス数

CONSOLE_NO = 1  # 個体名
MASTER_NO = 1   # マスター名

# LED設定
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT    # LEDの数
LED_PIN = 18    # GPIO設定
LED_FREQ_HZ = 800000    # 周波数
LED_DMA = 10    # DMA設定
LED_BRIGHTNESS = 10     # 明るさ
LED_INVERT = False      # 信号反転
LED_CHANNEL = 0     # チャンネル設定

# ジグザグ配線の設定
def zigzag_matrix(x,y):
    if y % 2 == 0:  # 偶数列
        return y * MATRIX_WIDTH + x
    else:           # 奇数列
        return y * MATRIX_HEIGHT + (MATRIX_WIDTH - 1 - x)

def single_function():
    """単体機能"""
    # LED setting
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    try:
        while True:
            # Get dynamic parameters
            point_count, speed, dynamic_value = pressure_parameters()
            print(f"Dynamic value: {dynamic_value}, Points: {point_count}, Speed: {speed}")

            # Generate random starting points and their colors
            points = []
            for _ in range(point_count):  # Adjust number of points dynamically
                x = random.randint(0, MATRIX_WIDTH - 1)
                y = random.randint(0, MATRIX_HEIGHT - 1)
                color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                points.append((x, y, color))

            # Choose a random target point
            target_x = random.randint(0, MATRIX_WIDTH - 1)
            target_y = random.randint(0, MATRIX_HEIGHT - 1)

            print(f"Target position: ({target_x}, {target_y})")

            # Move all points toward the target simultaneously
            update_positions(points, target_x, target_y, strip, speed)

            # Pause before resetting
            time.sleep(2)

            # Clear the matrix
            clear_matrix(strip)

    except KeyboardInterrupt:
        # Clear on exit
        clear_matrix(strip)

def multi_function():
    """複数機能"""
    if CONSOLE_NO == MASTER_NO:     # マスター
        master()
    else:   # スレーブ
        slave()

# マスター
def master():
    return

# スレーブ
def slave():
    return


def main():
    """
    if MATRIX_ROWS > 2 and MATRIX_COLS > 2:     # 単体機能
        single_function()
    else:   # 複数機能
        multi_function()
    """

if __name__ == "__main__":
    main()