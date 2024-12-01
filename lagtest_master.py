"""
ラグテスト用コード
スレーブは test3_slave.pyを動かす
"""
import socket
import json
import math
import time
from rpi_ws281x import PixelStrip, Color

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

# マトリクスLEDの配置設定 (4x3)
MATRIX_WIDTH = 4
MATRIX_HEIGHT = 3
LED_PER_PANEL = 16

# スレーブIPリスト
slave_ips = ['192.168.10.61', '192.168.10.62', '192.168.10.63', '192.168.10.64']  # 必要に応じて追加

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def draw_master(coordinates, color):
    """マスターが自身の範囲内の座標を描画する。"""
    clear_screen()
    for global_x, global_y in coordinates:
        if 0 <= global_x < LED_PER_PANEL and 0 <= global_y < LED_PER_PANEL:
            index = global_y * LED_PER_PANEL + global_x
            strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

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

def rotate_point(x, y, angle, cx, cy):
    """指定の点を中心 (cx, cy) 周りに回転させる。"""
    radians = math.radians(angle)
    cos_theta = math.cos(radians)
    sin_theta = math.sin(radians)
    nx = cos_theta * (x - cx) - sin_theta * (y - cy) + cx
    ny = sin_theta * (x - cx) + cos_theta * (y - cy) + cy
    return round(nx), round(ny)

def generate_triangle(cx, cy, size, angle):
    """中心 (cx, cy) を中心とした回転三角形の頂点を生成する。"""
    vertices = [
        (cx, cy - size),  # 上
        (cx - size, cy + size),  # 左下
        (cx + size, cy + size)   # 右下
    ]
    return [rotate_point(x, y, angle, cx, cy) for x, y in vertices]

def calculate_slave_coordinates(global_coordinates):
    """各スレーブに送る描画範囲を計算。"""
    slave_coordinates = [[] for _ in range(MATRIX_WIDTH * MATRIX_HEIGHT)]
    for x, y in global_coordinates:
        panel_x = x // LED_PER_PANEL
        panel_y = y // LED_PER_PANEL
        panel_index = panel_y * MATRIX_WIDTH + panel_x
        local_x = x % LED_PER_PANEL
        local_y = y % LED_PER_PANEL
        slave_coordinates[panel_index].append((local_x, local_y))
    return slave_coordinates

def point_in_triangle(pt, tri):
    """点が三角形内にあるかを判定する。"""
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    b1 = sign(pt, tri[0], tri[1]) < 0.0
    b2 = sign(pt, tri[1], tri[2]) < 0.0
    b3 = sign(pt, tri[2], tri[0]) < 0.0
    return b1 == b2 == b3

def draw_frame(angle):
    """アニメーションフレームを描画。"""
    cx, cy = 32, 24  # 全体の中央 (4x3配置の場合)
    size = 16  # 三角形のサイズ
    triangle = generate_triangle(cx, cy, size, angle)

    # 三角形を塗りつぶす（全座標を計算）
    coordinates = []
    for y in range(MATRIX_HEIGHT * LED_PER_PANEL):
        for x in range(MATRIX_WIDTH * LED_PER_PANEL):
            if point_in_triangle((x, y), triangle):
                coordinates.append((x, y))

    # マスターの描画
    master_coordinates = [(x, y) for x, y in coordinates if x < LED_PER_PANEL and y < LED_PER_PANEL]
    draw_master(master_coordinates, [0, 255, 0])  # 緑色

    # スレーブへの指示
    slave_coordinates = calculate_slave_coordinates(coordinates)
    for i, ip in enumerate(slave_ips):
        command = {
            "type": "draw",
            "coordinates": slave_coordinates[i],
            "color": [0, 255, 0]  # 緑色
        }
        send_command(command, [ip])

if __name__ == '__main__':
    clear_screen()
    angle = 0
    while True:
        draw_frame(angle)
        angle = (angle + 10) % 360  # 10度ずつ回転
        time.sleep(0.1)  # アニメーションの速度
