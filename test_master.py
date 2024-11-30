import socket
from rpi_ws281x import PixelStrip, Color

# LED設定（スレーブと同じ設定を使用）
LED_COUNT = 512  # 16x32 = 512個のLED
LED_PIN = 18  # データピン
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

def set_pixel(x, y, color):
    """(x, y)座標に対応するピクセルに色を設定する。"""
    if 0 <= x < 32 and 0 <= y < 16:  # マスター用固定サイズ
        index = y * 32 + x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))

def draw_triangle(color):
    """左上から始まる大きな三角形を描画。"""
    for y in range(16):
        for x in range(y + 1):
            set_pixel(x, y, color)
    strip.show()

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def send_command(command, ip_list, port=12345):
    """複数のスレーブにコマンドを送信する。"""
    for ip in ip_list:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                client_socket.sendall(command.encode('utf-8'))
                print(f"Sent '{command}' to {ip}")
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")

if __name__ == '__main__':
    # スレーブのIPリスト
    slave_ips = ['192.168.1.100', '192.168.1.101']

    # 画面をクリア
    clear_screen()

    # 三角形を描画（マスター用）
    draw_triangle((0, 0, 255))  # 青色

    # スレーブにコマンドを送信
    send_command('TRIANGLE', slave_ips)
