"""
ラグテスト用コード
回転する三角形を描画する
スレーブは test4_slave.pyを実行する
"""

import socket
import json
import math
import time
from rpi_ws281x import PixelStrip, Color

# スレーブのIPリスト
slave_ips = ['192.168.10.61']  # 必要に応じて追加

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
MATRIX_WIDTH = 2
MATRIX_HEIGHT = 1
LED_PER_PANEL = 16
TOTAL_WIDTH = LED_PER_PANEL * MATRIX_WIDTH
TOTAL_HEIGHT = LED_PER_PANEL * MATRIX_HEIGHT

# 中心座標と回転のための設定
center_x,center_y = TOTAL_WIDTH / 2, TOTAL_HEIGHT / 2   # マトリクスの中心
# center_x,center_y = 8, 8
radius = 5  # 三角形の長点が中心からどれだけ離れるか
angle_step = math.radius(10)    # 1フレームで回転する角度

def zigzag_transform(x, y, width = LED_PER_PANEL):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:  # 奇数行の場合
        x = width - 1 - x
    return x, y

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def draw_master(coordinates, color):
    """マスターが自身の範囲内の座標を描画する。"""
    for global_x, global_y in coordinates:
        if 0 <= global_x < LED_PER_PANEL and 0 <= global_y < LED_PER_PANEL:
            global_x, global_y = zigzag_transform(global_x, global_y)
            index = global_y * LED_PER_PANEL + global_x
            strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

def send_command(command, ip_list, port=12345):
    """スレーブにコマンドを送信する。"""
    for ip in ip_list:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                data = json.dumps(command).encode('utf-8')  # JSONデータをエンコード
                client_socket.sendall(data)  # 正しくデータを送信
                print(f"Sent command to {ip}")
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")

def calculate_slave_coordinates(global_coordinates):
    """各スレーブに送る描画範囲を計算。"""
    slave_coordinates = [[] for _ in range(MATRIX_WIDTH * MATRIX_HEIGHT)]
    for x, y in global_coordinates:
        x,y = zigzag_transform(x,y)     # ジグザグ配列修正
        panel_x = x // LED_PER_PANEL
        panel_y = y // LED_PER_PANEL
        panel_index = panel_y * MATRIX_WIDTH + panel_x
        local_x = x % LED_PER_PANEL
        local_y = y % LED_PER_PANEL
        slave_coordinates[panel_index].append((local_x, local_y))
    return slave_coordinates


def calculate_triangle_vertices(angle):
    """現在の回転角度に基づいて三角形の頂点を計算"""
    vertices = []
    for i in range(3):  # 三角形の3つの頂点
        theta = angle + i * (2 * math.pi / 3)
        x = int(center_x + radius * math.cos(theta))
        y = int(center_y + radius * math.sin(theta))
        vertices.append((x, y))
    return vertices

def draw_frame(angle):
    """現在の回転角度で三角形を描画"""
    # 三角形の頂点を計算
    vertices = calculate_triangle_vertices(angle)
    # 頂点から三角形の全座標を計算 (簡略化のため辺を点で近似)
    coordinates = []
    for i in range(len(vertices)):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % len(vertices)]
        # 直線を点で近似
        steps = max(abs(x2 - x1), abs(y2 - y1))
        for t in range(steps + 1):
            x = x1 + (x2 - x1) * t // steps
            y = y1 + (y2 - y1) * t // steps
            coordinates.append((x, y))

    # マスターの範囲
    master_coordinates = [
        (x, y) for x, y in coordinates
        if 0 <= x < LED_PER_PANEL and 0 <= y < LED_PER_PANEL
    ]
    draw_master(master_coordinates, [0, 255, 0])  # 緑色

    # スレーブの範囲を計算して送信
    slave_coordinates = calculate_slave_coordinates(coordinates)
    for i, ip in enumerate(slave_ips):
        command = {
            "type": "draw",
            "coordinates": slave_coordinates[i],
            "color": [0, 255, 0]
        }
        send_command(command, [ip])

# アニメーションループ
if __name__ == "__main__":
    clear_screen()
    current_angle = 0
    while True:
        draw_frame(current_angle)
        current_angle += angle_step
        time.sleep(0.1)  # ラグの確認用の遅延