import socket
import json
import math
import random
from time import sleep
from rpi_ws281x import PixelStrip, Color

# マトリクス設定
MATRIX_WIDTH = 64  # 全体の横幅 (例: 4枚 x 16)
MATRIX_HEIGHT = 48  # 全体の縦幅 (例: 3枚 x 16)
LED_PER_PANEL = 16

# LED設定
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

# スレーブIPリスト
slave_ips = ['192.168.10.61', '192.168.10.62', '192.168.10.63', '192.168.10.64']

# LEDストリップ初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def clear_screen():
    """画面を消灯する。"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def zigzag_matrix(x, y):
    """ジグザグ配線のインデックス計算。"""
    if y % 2 == 0:  # 偶数行
        return y * MATRIX_WIDTH + x
    else:  # 奇数行
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

def send_command(command, ip_list, port=12345):
    """スレーブにコマンドを送信する。"""
    for ip in ip_list:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                data = json.dumps(command).encode('utf-8')
                client_socket.sendall(data)
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")

def circle_pixels(xc, yc, radius):
    """指定された中心と半径の円の座標を生成。"""
    x = 0
    y = radius
    d = 1 - radius
    pixels = []

    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < MATRIX_WIDTH and 0 <= yc + dy < MATRIX_HEIGHT:
                pixels.append((xc + dx, yc + dy))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1

    return pixels

def draw_frame(circles):
    """フレームを描画する。"""
    global_pixels = set()
    circle_pixels_by_slave = {ip: [] for ip in slave_ips}

    for circle in circles:
        xc, yc, radius, color = circle
        pixels = circle_pixels(xc, yc, radius)

        for x, y in pixels:
            pixel_index = zigzag_matrix(x, y)
            global_pixels.add(pixel_index)
            if x < LED_PER_PANEL:
                strip.setPixelColor(pixel_index, color)
            else:
                slave_ip = slave_ips[(x // LED_PER_PANEL) % len(slave_ips)]
                circle_pixels_by_slave[slave_ip].append((x, y, color))

    # スレーブに指示を送信
    for ip, pixels in circle_pixels_by_slave.items():
        command = {
            "type": "draw",
            "pixels": pixels
        }
        send_command(command, [ip])

    strip.show()

def mix_colors(color1, color2):
    """色を混ぜる。"""
    r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
    r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
    r = (r1 + r2) // 2
    g = (g1 + g2) // 2
    b = (b1 + b2) // 2
    return Color(r, g, b)

if __name__ == '__main__':
    clear_screen()

    try:
        while True:
            # ランダムな円を生成
            circles = [
                (random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1), 0, Color(255, 0, 0)),
                (random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1), 0, Color(0, 0, 255))
            ]

            for frame in range(16):  # 半径16まで拡大
                for i, circle in enumerate(circles):
                    xc, yc, radius, color = circle
                    circles[i] = (xc, yc, radius + 1, color)

                draw_frame(circles)
                sleep(0.1)

    except KeyboardInterrupt:
        clear_screen()
