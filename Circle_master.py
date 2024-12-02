import socket
import json
from rpi_ws281x import PixelStrip, Color
from time import sleep

# LED設定
LED_COUNT = 256  # 16x16
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False

# PixelStripの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# マトリクスの設定
MATRIX_WIDTH = 32  # マスターとスレーブの合計幅
MATRIX_HEIGHT = 16
LED_PER_PANEL = 16

# スレーブのIPアドレス
SLAVE_IPS = ["192.168.10.61", "192.168.10.62"]


# ジグザグ補正
def zigzag_transform(x, y, width=16):
    if y % 2 == 1:
        x = width - 1 - x
    return x, y


# 円の座標計算
def calculate_circle_pixels(center_x, center_y, radius):
    pixels = []
    x = 0
    y = radius
    d = 1 - radius
    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            px, py = center_x + dx, center_y + dy
            if 0 <= px < MATRIX_WIDTH and 0 <= py < MATRIX_HEIGHT:
                pixels.append((px, py))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return pixels


# 衝突判定
def detect_collision(circle1, circle2):
    return list(set(circle1) & set(circle2))


# 描画命令をスレーブに送信
def send_command(command, ip):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, 12345))
            sock.sendall(json.dumps(command).encode("utf-8"))
    except Exception as e:
        print(f"Failed to send command to {ip}: {e}")


# マスター範囲内の描画
def draw_master(pixels, color):
    for x, y in pixels:
        if x < LED_PER_PANEL and y < LED_PER_PANEL:
            index = y * LED_PER_PANEL + x
            strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()


# スレーブ用描画指示
def distribute_to_slaves(global_pixels, color):
    slave_areas = {ip: [] for ip in SLAVE_IPS}
    for x, y in global_pixels:
        if x >= LED_PER_PANEL:  # マスターの右側
            slave_index = (x - LED_PER_PANEL) // LED_PER_PANEL
            if 0 <= slave_index < len(SLAVE_IPS):
                slave_areas[SLAVE_IPS[slave_index]].append((x - LED_PER_PANEL, y))
    for ip, pixels in slave_areas.items():
        command = {"type": "draw", "coordinates": pixels, "color": color}
        send_command(command, ip)


# 中心から消去
def delete_circle(pixels, center, color, delay=50):
    cx, cy = center
    distances = sorted(pixels, key=lambda p: ((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5)
    for x, y in distances:
        if x < LED_PER_PANEL:
            index = y * LED_PER_PANEL + x
            strip.setPixelColor(index, Color(0, 0, 0))
        else:
            for ip in SLAVE_IPS:
                send_command({"type": "clear_pixel", "coordinates": [(x, y)]}, ip)
        strip.show()
        sleep(delay / 1000)


# メイン処理
if __name__ == "__main__":
    clear_screen()
    try:
        center1, center2 = (8, 8), (24, 8)
        radius = 0
        max_radius = min(MATRIX_WIDTH, MATRIX_HEIGHT) // 2
        color1 = [255, 0, 0]
        color2 = [0, 0, 255]

        while radius <= max_radius:
            circle1 = calculate_circle_pixels(center1[0], center1[1], radius)
            circle2 = calculate_circle_pixels(center2[0], center2[1], radius)

            collision = detect_collision(circle1, circle2)
            if collision:
                color1, color2 = [0, 255, 0], [0, 255, 0]

            draw_master(circle1, color1)
            draw_master(circle2, color2)
            distribute_to_slaves(circle1, color1)
            distribute_to_slaves(circle2, color2)

            if collision:
                delete_circle(circle1, center1, color1)
                delete_circle(circle2, center2, color2)
                break

            radius += 1
            sleep(0.1)
    except KeyboardInterrupt:
        clear_screen()
