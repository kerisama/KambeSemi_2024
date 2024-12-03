import socket
import json
import time
from rpi_ws281x import PixelStrip, Color
import random

# LED設定
LED_COUNT = 256  # 16x16
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16
MATRIX_WIDTH = 2
MATRIX_HEIGHT = 1

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# スレーブ設定
slave_ips = ['192.168.10.61', '192.168.10.62']  # 必要に応じて追加
slave_port = 12345


# ジグザグ補正
def zigzag_transform(x, y, width=LED_PER_PANEL):
    if y % 2 == 1:
        x = width - 1 - x
    return x, y


def clear_screen():
    """LEDマトリクスを消灯"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


# 描画座標計算
def circle_pixels(xc, yc, radius):
    x = 0
    y = radius
    d = 1 - radius
    pixels = []
    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < LED_PER_PANEL and 0 <= yc + dy < LED_PER_PANEL:
                pixels.append((xc + dx, yc + dy))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return pixels


def send_command(command, ip_list):
    for ip in ip_list:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, slave_port))
                client_socket.sendall(json.dumps(command).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send command to {ip}: {e}")


# 衝突処理
def colliding_circles(xc1, yc1, color1, xc2, yc2, color2, max_radius):
    for radius in range(max_radius):
        pixels1 = circle_pixels(xc1, yc1, radius)
        pixels2 = circle_pixels(xc2, yc2, radius)

        collision = set(pixels1) & set(pixels2)  # 衝突検知

        for px, py in collision:
            strip.setPixelColor(py * LED_PER_PANEL + px, Color(255, 0, 0))  # 衝突地点
        for px, py in pixels1:
            if (px, py) not in collision:
                strip.setPixelColor(py * LED_PER_PANEL + px, color1)
        for px, py in pixels2:
            if (px, py) not in collision:
                strip.setPixelColor(py * LED_PER_PANEL + px, color2)

        strip.show()
        time.sleep(0.05)
        if collision:
            break

    time.sleep(0.5)

    # 円を消去
    for px, py in pixels1 + pixels2:
        strip.setPixelColor(py * LED_PER_PANEL + px, Color(0, 0, 0))
    strip.show()


if __name__ == '__main__':
    clear_screen()
    try:
        while True:
            xc1, yc1 = random.randint(0, LED_PER_PANEL - 1), random.randint(0, LED_PER_PANEL - 1)
            xc2, yc2 = random.randint(0, LED_PER_PANEL - 1), random.randint(0, LED_PER_PANEL - 1)

            color1 = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            color2 = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            colliding_circles(xc1, yc1, color1, xc2, yc2, color2, max_radius=LED_PER_PANEL // 2)

    except KeyboardInterrupt:
        clear_screen()
