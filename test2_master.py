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

# マスターの担当領域（1番の役割）
MASTER_ORIGIN_X = 0
MASTER_ORIGIN_Y = 0

def set_pixel_local(x, y, color):
    """ローカル座標でピクセルに色を設定する。"""
    if 0 <= x < 16 and 0 <= y < 16:  # マスターの範囲
        index = y * 16 + x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def draw_master(coordinates, color):
    """マスターが自身の範囲内の座標を描画する。"""
    for global_x, global_y in coordinates:
        local_x = global_x - MASTER_ORIGIN_X
        local_y = global_y - MASTER_ORIGIN_Y
        if 0 <= local_x < 16 and 0 <= local_y < 16:  # マスターの範囲内
            set_pixel_local(local_x, local_y, color)
    strip.show()

def send_command(command, ip_list, port=12345):
    """スレーブにコマンドを送信する。"""
    for ip in ip_list:
        try:
            # スレーブに送信するために座標にオフセットを加える
            if ip == '192.168.10.61':  # スレーブ1のIP
                offset_x = 16  # スレーブ1のx方向オフセット
                offset_y = 0   # スレーブ1のy方向オフセット
                # 座標にオフセットを加える
                modified_coordinates = [(x + offset_x, y + offset_y) for (x, y) in command["coordinates"]]
                command["coordinates"] = modified_coordinates
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                data = json.dumps(command).encode('utf-8')  # JSONデータをエンコード
                client_socket.sendall(data)  # 正しくデータを送信
                print(f"Sent command to {ip}")
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")


if __name__ == '__main__':
    # スレーブのIPリスト
    slave_ips = ['192.168.10.61']  # スレーブ1のIP

    # マスターが描画する座標（0,0から15,15まで）
    master_coordinates = [(x, y) for y in range(16) for x in range(y + 1)]

    # スレーブ1に送る座標（16,0から31,15まで）
    slave_coordinates = [(x + 16, y) for y in range(16) for x in range(y + 1)]

    # 描画色
    color = [0, 0, 255]  # 青色

    # 画面をクリア
    clear_screen()

    # マスターが自身の領域を描画
    draw_master(master_coordinates, color)

    # スレーブ1にコマンドを送信
    command = {
        "type": "draw",
        "coordinates": slave_coordinates,
        "color": color
    }
    send_command(command, slave_ips)

    
