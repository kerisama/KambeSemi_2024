import socket
import json
from rpi_ws281x import PixelStrip, Color
import random
from time import sleep

# LED設定
LED_COUNT = 256  # 16x16
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

# マトリクス設定
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16
LED_PER_PANEL = 16

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# スレーブのIPリスト
slave_ips = ['192.168.10.61', '192.168.10.62', '192.168.10.63', '192.168.10.64']  # 必要に応じて追加

def zigzag_transform(x, y):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:  # 奇数行の場合
        x = LED_PER_PANEL - 1 - x
    return y * LED_PER_PANEL + x

def clear_screen():
    """LEDマトリクスを消灯"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def calculate_circle(xc, yc, radius):
    """円のピクセルを計算"""
    x = 0
    y = radius
    d = 1 - radius
    pixels = []

    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            px, py = xc + dx, yc + dy
            if 0 <= px < MATRIX_WIDTH and 0 <= py < MATRIX_HEIGHT:
                pixels.append((px, py))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return pixels

def detect_collisions(circle1, circle2):
    """円同士の衝突を検出"""
    return list(set(circle1) & set(circle2))

def mix_colors(color1, color2):
    """色を混ぜる"""
    r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
    r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
    r = (r1 + r2) // 2
    g = (g1 + g2) // 2
    b = (b1 + b2) // 2
    return Color(r, g, b)

def distribute_to_slaves(circle1, circle2):
    """スレーブ用のコマンドを計算"""
    global_pixels = circle1 + circle2
    slave_coordinates = [[] for _ in range(len(slave_ips))]

    for x, y in global_pixels:
        panel_x = x // LED_PER_PANEL
        panel_y = y // LED_PER_PANEL
        panel_index = panel_y * (MATRIX_WIDTH // LED_PER_PANEL) + panel_x
        local_x = x % LED_PER_PANEL
        local_y = y % LED_PER_PANEL
        if panel_index < len(slave_ips):
            slave_coordinates[panel_index].append((local_x, local_y))
    return slave_coordinates

def draw_pixels(strip, pixels, color):
    """指定されたピクセルを描画"""
    for x, y in pixels:
        index = zigzag_transform(x, y)
        strip.setPixelColor(index, color)
    strip.show()

def send_to_slaves(slave_data, color):
    """スレーブに描画コマンドを送信"""
    for i, ip in enumerate(slave_ips):
        command = {
            "type": "draw",
            "coordinates": slave_data[i],
            "color": [color.red, color.green, color.blue]
        }
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, 12345))
                client_socket.sendall(json.dumps(command).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")

def main():
    max_radius = MATRIX_WIDTH // 4
    clear_screen()

    while True:
        # ランダムな円の中心と色
        xc1, yc1 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
        xc2, yc2 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
        color1 = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        color2 = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        for radius in range(max_radius):
            # 円を計算
            circle1 = calculate_circle(xc1, yc1, radius)
            circle2 = calculate_circle(xc2, yc2, radius)

            # 衝突検出
            collisions = detect_collisions(circle1, circle2)

            # マスターで描画
            draw_pixels(strip, circle1, color1)
            draw_pixels(strip, circle2, color2)
            if collisions:
                draw_pixels(strip, collisions, mix_colors(color1, color2))

            # スレーブに送信
            slave_data = distribute_to_slaves(circle1, circle2)
            send_to_slaves(slave_data, color1 if not collisions else mix_colors(color1, color2))

            sleep(0.1)

        # 次のループに備え消去
        clear_screen()

if __name__ == "__main__":
    main()
