import socket
import json
import random
import time
from rpi_ws281x import PixelStrip, Color

# LED設定
LED_COUNT = 256
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# ジグザグ補正
def zigzag_transform(x, y, width=LED_PER_PANEL):
    if y % 2 == 1:  # 奇数行
        x = width - 1 - x
    return x, y

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
                client_socket.connect((ip, 12345))
                client_socket.sendall(json.dumps(command).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send command to {ip}: {e}")

def clear_screen():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def draw_and_animate_circles(strip, xc1, yc1, xc2, yc2, color1, color2, max_radius):
    pixels_circle1 = []
    pixels_circle2 = []

    # アニメーションで円を拡大
    for radius in range(max_radius):
        new_circle1 = circle_pixels(xc1, yc1, radius)
        new_circle2 = circle_pixels(xc2, yc2, radius)

        # 衝突判定
        collision = set(new_circle1) & set(new_circle2)
        for x, y in collision:
            strip.setPixelColor(y * LED_PER_PANEL + x, Color(255, 0, 0))  # 衝突部分を赤に
        for x, y in new_circle1:
            if (x, y) not in collision:
                strip.setPixelColor(y * LED_PER_PANEL + x, color1)
        for x, y in new_circle2:
            if (x, y) not in collision:
                strip.setPixelColor(y * LED_PER_PANEL + x, color2)

        pixels_circle1.extend(new_circle1)
        pixels_circle2.extend(new_circle2)
        strip.show()
        time.sleep(0.1)

        if collision:
            break

    # 消えるアニメーション
    delete_circle(strip, pixels_circle1, (xc1, yc1))
    delete_circle(strip, pixels_circle2, (xc2, yc2))

def delete_circle(strip, circle_pixels, center):
    distances = sorted(circle_pixels, key=lambda p: ((p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2) ** 0.5)
    for x, y in distances:
        strip.setPixelColor(y * LED_PER_PANEL + x, Color(0, 0, 0))
        strip.show()
        time.sleep(0.01)

if __name__ == '__main__':
    clear_screen()
    try:
        while True:
            xc1, yc1 = random.randint(0, LED_PER_PANEL - 1), random.randint(0, LED_PER_PANEL - 1)
            xc2, yc2 = random.randint(0, LED_PER_PANEL - 1), random.randint(0, LED_PER_PANEL - 1)
            color1 = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            color2 = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            draw_and_animate_circles(strip, xc1, yc1, xc2, yc2, color1, color2, max_radius=8)
    except KeyboardInterrupt:
        clear_screen()
