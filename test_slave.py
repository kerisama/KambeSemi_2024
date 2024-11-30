import socket
from rpi_ws281x import PixelStrip, Color

# LED設定（スレーブ固有）
LED_COUNT = 512  # 16x32 = 512個のLED
LED_PIN = 18  # データピン
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

def set_pixel(x, y, color, offset_x=0, offset_y=0):
    """スレーブのオフセットを考慮したピクセルに色を設定する。"""
    global LED_COUNT
    if 0 <= x - offset_x < 32 and 0 <= y - offset_y < 16:
        index = (y - offset_y) * 32 + (x - offset_x)
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))

def draw_triangle(color, offset_x=0, offset_y=0):
    """左上から始まる三角形を描画。"""
    for y in range(offset_y, offset_y + 16):
        for x in range(offset_x, offset_x + (y - offset_y + 1)):
            set_pixel(x, y, color, offset_x, offset_y)
    strip.show()

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def handle_command(command):
    """受信したコマンドに応じて処理を実行する。"""
    if command == 'TRIANGLE':
        draw_triangle((0, 255, 0))  # 緑の三角形
    elif command == 'CLEAR':
        clear_screen()
    else:
        print(f"未知のコマンド: {command}")

def start_server(port=12345, offset_x=0, offset_y=0):
    """スレーブがコマンドを待機するサーバー。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen()
        print("スレーブが待機中...")
        while True:
            conn, _ = server_socket.accept()
            with conn:
                data = conn.recv(1024).decode('utf-8')
                if data:
                    print(f"Received command: {data}")
                    handle_command(data)

if __name__ == '__main__':
    clear_screen()  # 初期化で消灯
    # スレーブのマトリクスオフセットを指定
    start_server(offset_x=0, offset_y=0)
