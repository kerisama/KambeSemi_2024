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
LED_PER_PANEL = 16  # 列ごとのLED数 (16)

# スレーブ1の担当領域
SLAVE_ORIGIN_X = LED_PER_PANEL * SLAVE_ROWS  # x方向のオフセット (16~)
SLAVE_ORIGIN_Y = LED_PER_PANEL * SLAVE_COLS  # y方向のオフセット (0~)


def zigzag_transform(x, y, width=16):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:  # 奇数行の場合
        x = width - 1 - x
    return x + y * width


def set_pixel_local(x, y, color):
    """ローカル座標でピクセルに色を設定する。"""
    if 0 <= x < LED_PER_PANEL and 0 <= y < LED_PER_PANEL:
        zigzag_x,zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x
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
            # グローバル座標をローカル座標に変換
            local_x = global_x - SLAVE_ORIGIN_X
            local_y = global_y - SLAVE_ORIGIN_Y

            if 0 <= local_x < LED_PER_PANEL and 0 <= local_y < LED_PER_PANEL:  # 自分の範囲内
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
                    data += chunk

                try:
                    command = json.loads(data.decode('utf-8'))  # JSONデータとしてデコード
                    handle_command(command)
                except json.JSONDecodeError as e:
                    print(f"JSONデコードエラー: {e}")


if __name__ == '__main__':
    clear_screen()  # 初期化で消灯
    start_server()  # サーバー開始
