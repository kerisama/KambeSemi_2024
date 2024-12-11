import socket
import json
import threading
from rpi_ws281x import PixelStrip, Color
import time
import datetime

# LED設定
LED_COUNT = 256  # 16x16
LED_PIN = 10
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16  # 列ごとのLED数 (16)
LED_CHANNEL = 0



MASTER_IP = "192.168.10.60"
MASTER_PORT = 5000

# スレーブの列・行番号 (マスターを0,0とする)
SLAVE_ROWS = 1  # 横方向
SLAVE_COLS = 0  # 縦方向
# スレーブ1の担当領域
SLAVE_ORIGIN_X = LED_PER_PANEL * SLAVE_ROWS  # x方向のオフセット
SLAVE_ORIGIN_Y = LED_PER_PANEL * SLAVE_COLS  # y方向のオフセット

# Matrix setup
MATRIX_GLOBAL_WIDTH = (SLAVE_ROWS + 1) * LED_PER_PANEL
MATRIX_GLOBAL_HEIGHT = (SLAVE_COLS + 1) * LED_PER_PANEL

# 円の幅
CIRCLE_WIDTH = 5

class MasterConnection:
    def __init__(self, master_ip, master_port, row, column):
        self.master_ip = master_ip
        self.master_port = master_port
        self.row = row
        self.column = column
        self.client_socket = None
        self.client_id = self.get_client_id()

    def get_client_id(self):
        """ユニークなクライアントIDを生成"""
        return f"Device_{socket.gethostname()}"

    def send_to_master(self, data: dict):
        """任意のデータをマスターに送信"""
        try:
            if self.client_socket:
                self.client_socket.send(json.dumps(data).encode())
                print(f"Sent to master: {data}")
            else:
                print("Client socket is not connected.")
        except Exception as e:
            print(f"Failed to send to master: {e}")

    def listen_for_master_data(self):
        """マスターからのデータを受信"""
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                try:
                    received_data = json.loads(data.decode())
                    print(f"Received from master: {received_data}")
                    # 受信できたらデータの処理をする
                    self.handle_command(received_data)
                except json.JSONDecodeError:
                    print("Failed to decode data from master")
        except Exception as e:
            print(f"Error receiving from master: {e}")
        finally:
            self.client_socket.close()

    def handle_command(self, command):
        # 受信したコマンドに応じて描画処理を実行する
        if command["type"] == "draw":
            x = command["x"]
            y = command["y"]
            colors = command["colors"]
            max_radius = command["max_radius"]
            animation_slave_thread = threading.Thread(target=animate_slave_circles, args=(x, y, colors, max_radius,))
            animation_slave_thread.daemon = True  # メインが終われば終わる
            animation_slave_thread.start()
        elif command["type"] == "clear":
            clear_screen()

    def setup_slave(self):
        """スレーブをマスターと接続（接続に失敗した場合は再接続）"""
        while True:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.master_ip, self.master_port))
                print(f"Connected to master at {self.master_ip}:{self.master_port}")

                # 接続時に初期データを送信
                init_data = {
                    "type": "init",
                    "client_id": self.client_id,
                    "position": {"row": self.row, "column": self.column}
                }
                self.send_to_master(init_data)

                # マスターからのデータを受信するスレッドを開始
                listener_thread = threading.Thread(target=self.listen_for_master_data)
                listener_thread.daemon = True
                listener_thread.start()

                break  # 接続成功後はループを抜ける

            except (socket.error, Exception) as e:
                print(f"Error connecting to master: {e}. Retrying in 2 seconds...")
                time.sleep(2)  # 5秒後に再試行

        # マスターとの接続が切れた場合も再接続を試みる
        self.reconnect_if_disconnected()

    def reconnect_if_disconnected(self):
        """接続が切れた場合に再接続を試みる"""
        while True:
            if self.client_socket is None or self.client_socket.fileno() == -1:  # ソケットが閉じられている場合
                print("Connection lost. Reconnecting...")
                self.setup_slave()  # 再接続を試みる
            time.sleep(5)

    def close_connection(self):
        """マスターとの接続を切る"""
        if self.client_socket:
            self.client_socket.close()
            print("Disconnected from master")

def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def zigzag_transform(x, y, width=16):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:
        x = LED_PER_PANEL - 1 - x
    return x, y

def circle_pixels(xc, yc, radius):
    """Generate circle pixels for a given center and radius."""
    x, y = 0, radius
    d = 1 - radius
    pixels = []

    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < MATRIX_GLOBAL_WIDTH and 0 <= yc + dy < MATRIX_GLOBAL_HEIGHT:
                pixels.append((xc + dx, yc + dy))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return pixels

def draw_slave(frame_pixels, color):
    # Draw a single frame of animation.
    slave_pixels = [p for p in frame_pixels if
                    SLAVE_ORIGIN_X <= p[0] < SLAVE_ORIGIN_X + 16 and SLAVE_ORIGIN_Y <= p[1] < SLAVE_ORIGIN_Y + 16]

    # Draw slave pixels
    for x, y in slave_pixels:
        # ローカル座標に変換
        x -= SLAVE_ORIGIN_X
        y -= SLAVE_ORIGIN_Y
        # ジグザグ変換
        zigzag_x, zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

def animate_slave_circles(xc, yc, colors, max_radius):
    radius = 0
    clear_radius = 0
    print("center of the circle: x:%d, y:%d" % (xc - SLAVE_ORIGIN_X, yc - SLAVE_ORIGIN_Y))
    # 円の描画
    while True:
        if clear_radius == max_radius:
            break
        if radius < max_radius:
            circle = circle_pixels(xc, yc, radius)
            color = colors[radius]
            
            draw_slave(circle, color)

            radius += 1

        if radius > CIRCLE_WIDTH:
            clear_circle = circle_pixels(xc, yc, clear_radius)
            # 描画を消す
            draw_slave(clear_circle, [0, 0, 0])
            clear_radius += 1
        time.sleep(0.1)



if __name__ == '__main__':
    # PixelStripオブジェクトの初期化
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    strip.begin()

    clear_screen()

    master_connection = MasterConnection(MASTER_IP, MASTER_PORT, SLAVE_ROWS, SLAVE_COLS)
    # スレッドでマスター接続を開始
    master_thread = threading.Thread(target=master_connection.setup_slave)
    master_thread.daemon = True
    master_thread.start()

    # メインスレッドで他の処理が続行できるようにする
    # 任意のデータを送信する例
    try:
        while True:
            sensor_data = {
                "type": "sensor_data",
                "x": 17,
                "y": 4,
                "data_total": 3000
            }
            master_connection.send_to_master(sensor_data)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    finally:
        clear_screen()
        master_connection.close_connection()
