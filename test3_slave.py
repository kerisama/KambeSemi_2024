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

# スレーブの列・行番号 (マスターを0,0とする)
SLAVE_ROWS = 1  # 横方向
SLAVE_COLS = 0  # 縦方向

LED_PER_PANEL = 16

# スレーブ1の担当領域
SLAVE_ORIGIN_X = 16 * SLAVE_ROWS  # x方向のオフセット
SLAVE_ORIGIN_Y = 16 * SLAVE_COLS   # y方向のオフセット

# ジグザグ配列の修正
def zigzag_matrix(x, y):
    if y % 2 == 0:  # Even rows
        return y * LED_PER_PANEL + x
    else:  # Odd rows
        return y * LED_PER_PANEL + (LED_PER_PANEL - 1 - x)

def set_pixel_local(x, y, color):
    """ローカル座標でピクセルに色を設定する。"""
    if 0 <= x < 16 and 0 <= y < 16:  # スレーブの範囲
        index = zigzag_matrix(y * 16, x)
        # index = y * 16 + x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def handle_command(command):
    """受信したコマンドに応じて描画処理を実行する。"""
    if command["type"] == "draw":
        for global_x, global_y in command["coordinates"]:
            # スレーブのオフセットを考慮してローカル座標に変換
            local_x = global_x - SLAVE_ORIGIN_X
            local_y = global_y - SLAVE_ORIGIN_Y
            if 0 <= local_x < 16 and 0 <= local_y < 16:  # 自分の範囲内
                set_pixel_local(local_x, local_y, command["color"])
        strip.show()
    elif command["type"] == "clear":
        clear_screen()

def start_server(port=12345):
    """スレーブがコマンドを待機するサーバー。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen()
        print("スレーブが待機中...")
        while True:
            conn, _ = server_socket.accept()
            with conn:
                data = b""
                while True:
                    # データを受信する。サイズが十分でない場合は繰り返し受信
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk  # 受信したデータをバッファに追加

                try:
                    command = json.loads(data.decode('utf-8'))  # JSONデータとしてデコード
                    handle_command(command)
                except json.JSONDecodeError as e:
                    print(f"JSONデコードエラー: {e}")
                    print(f"受信したデータ: {data}")


if __name__ == '__main__':
    clear_screen()  # 初期化で消灯
    start_server()  # サーバー開始
