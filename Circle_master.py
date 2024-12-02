import socket
import json
from rpi_ws281x import PixelStrip, Color
from time import sleep
import math

# LED設定
LED_COUNT = 256  # 16x16
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# マトリクスLEDの配置設定 (2x1)
MATRIX_WIDTH = 32
MATRIX_HEIGHT = 16
LED_PER_PANEL = 16

# スレーブのIPアドレス
slave_ips = ["192.168.10.61", "192.168.10.62"]

def zigzag_transform(x, y, width=LED_PER_PANEL):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:
        x = width - 1 - x
    return x, y

def circle_pixels(center_x, center_y, radius):
    """円の座標を生成する"""
    x = 0
    y = radius
    d = 1 - radius
    pixels = []

    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            global_x = center_x + dx
            global_y = center_y + dy
            if 0 <= global_x < MATRIX_WIDTH and 0 <= global_y < MATRIX_HEIGHT:
                pixels.append((global_x, global_y))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return pixels

def detect_collision(circle1, circle2):
    """2つの円のピクセルの重複を検知"""
    return list(set(circle1) & set(circle2))

def send_command(command, ip_list, port=12345):
    """スレーブにコマンドを送信する"""
    for ip in ip_list:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                data = json.dumps(command).encode("utf-8")
                client_socket.sendall(data)
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")

def delete_circle(strip, pixels, center, wait_ms=50):
    """中心から円を消去するアニメーション"""
    cx, cy = center
    distances = [(math.sqrt((x - cx)**2 + (y - cy)**2), x, y) for x, y in pixels]
    distances.sort()  # 中心から遠い順にソート
    for _, x, y in distances:
        zigzag_x, zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x
        strip.setPixelColor(index, Color(0, 0, 0))
        strip.show()
        sleep(wait_ms / 1000.0)

def animate_circles():
    """円を広げるアニメーション"""
    center1 = (10, 8)
    center2 = (20, 8)
    max_radius = MATRIX_WIDTH // 2
    color1 = Color(255, 0, 0)
    color2 = Color(0, 0, 255)

    for radius in range(max_radius):
        circle1 = circle_pixels(center1[0], center1[1], radius)
        circle2 = circle_pixels(center2[0], center2[1], radius)
        collisions = detect_collision(circle1, circle2)

        for x, y in circle1:
            zigzag_x, zigzag_y = zigzag_transform(x, y)
            index = zigzag_y * LED_PER_PANEL + zigzag_x
            if (x, y) in collisions:
                strip.setPixelColor(index, Color(255, 255, 0))  # 衝突時の色
            else:
                strip.setPixelColor(index, color1)

        for x, y in circle2:
            zigzag_x, zigzag_y = zigzag_transform(x, y)
            index = zigzag_y * LED_PER_PANEL + zigzag_x
            if (x, y) in collisions:
                strip.setPixelColor(index, Color(255, 255, 0))  # 衝突時の色
            else:
                strip.setPixelColor(index, color2)

        strip.show()
        sleep(0.1)

        if collisions:
            delete_circle(strip, circle1, center1)
            delete_circle(strip, circle2, center2)
            break

if __name__ == "__main__":
    strip.show()
    animate_circles()
