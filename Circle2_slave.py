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

# スレーブの担当範囲
SLAVE_ROWS = 1  # 横方向のオフセット
SLAVE_COLS = 0  # 縦方向のオフセット
LED_PER_PANEL = 16

# オフセット計算
SLAVE_ORIGIN_X = SLAVE_ROWS * LED_PER_PANEL
SLAVE_ORIGIN_Y = SLAVE_COLS * LED_PER_PANEL

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# ジグザグ補正
def zigzag_transform(x, y, width=LED_PER_PANEL):
    if y % 2 == 1:  # 奇数行
        x = width - 1 - x
    return x, y

# LEDを消去
def clear_screen():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# ローカル描画
def draw_circle(coordinates, color):
    for x, y in coordinates:
        # ローカル範囲内のみ描画
        local_x = x - SLAVE_ORIGIN_X
        local_y = y - SLAVE_ORIGIN_Y
        if 0 <= local_x < LED_PER_PANEL and 0 <= local_y < LED_PER_PANEL:
            local_x, local_y = zigzag_transform(local_x, local_y)
            index = local_y * LED_PER_PANEL + local_x
            strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

# コマンドハンドラー
def handle_command(command):
    if command["type"] == "draw":
        coordinates = command["coordinates"]
        color = command["color"]
        draw_circle(coordinates, color)
    elif command["type"] == "clear":
        clear_screen()

# サーバー開始
def start_server(port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen()
        print("スレーブが待機中...")
        while True:
            conn, _ = server_socket.accept()
            with conn:
                data = b""
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk

                try:
                    command = json.loads(data.decode('utf-8'))
                    handle_command(command)
                except json.JSONDecodeError as e:
                    print(f"JSONデコードエラー: {e}")

if __name__ == '__main__':
    clear_screen()
    start_server()
