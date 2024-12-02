import socket
import json
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

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def draw_master(coordinates, color):
    """マスターが自身の範囲内の座標を描画する。"""
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
                data = json.dumps(command).encode('utf-8')  # JSONデータをエンコード
                client_socket.sendall(data)  # 正しくデータを送信
                print(f"Sent command to {ip}")
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")

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

if __name__ == '__main__':
    # スレーブのIPリスト
    slave_ips = ['192.168.10.61', '192.168.10.62', '192.168.10.63', '192.168.10.64']  # 必要に応じて追加

    # 描画対象座標（全体座標で三角形を生成）
    coordinates = []
    total_width = MATRIX_WIDTH * LED_PER_PANEL
    for y in range(MATRIX_HEIGHT * LED_PER_PANEL):
        for x in range(y + 1):
            coordinates.append((x, y))

    # 描画色
    color = [0, 0, 255]  # 青色

    # 画面をクリア
    clear_screen()

    # マスターが自身の領域を描画
    master_coordinates = [(x, y) for x, y in coordinates if x < LED_PER_PANEL and y < LED_PER_PANEL]
    draw_master(master_coordinates, color)

    # スレーブ用座標を計算して送信
    slave_coordinates = calculate_slave_coordinates(coordinates)
    for i, ip in enumerate(slave_ips):
        command = {
            "type": "draw",
            "coordinates": slave_coordinates[i],
            "color": color
        }
        send_command(command, [ip])
