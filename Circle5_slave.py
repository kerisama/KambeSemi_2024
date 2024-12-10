# Multifunc3_master
import socket
import json
import threading
from rpi_ws281x import PixelStrip, Color
import time

# LED設定
LED_COUNT = 256  # 16x16
LED_PIN = 10
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16  # 列ごとのLED数 (16)
LED_CHANNEL = 0

# PixelStripオブジェクトの初期化
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

MASTER_IP = "192.168.10.65"
MASTER_PORT = 5000

# スレーブの列・行番号 (マスターを0,0とする)
SLAVE_ROWS = 1  # 横方向
SLAVE_COLS = 1  # 縦方向
# スレーブ1の担当領域
SLAVE_ORIGIN_X = LED_PER_PANEL * SLAVE_ROWS  # x方向のオフセット
SLAVE_ORIGIN_Y = LED_PER_PANEL * SLAVE_COLS  # y方向のオフセット

# 円の幅
CIRCLE_WIDTH = 5


def zigzag_transform(x, y, width=16):
    """ジグザグ配列に変換する座標"""
    if y % 2 == 1:
        x = LED_PER_PANEL - 1 - x
    return x, y


def set_pixel_local(x, y, color):
    """ローカル座標でピクセルに色を設定する。"""

    index = y * 16 + x
    strip.setPixelColor(index, Color(color[0], color[1], color[2]))


def clear_screen():
    """LEDマトリクスを消灯。"""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


# 複数機能につかう関数
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

    # 円の描画
    while True:
        if clear_radius == max_radius:
            break
        # print("Draw Circle :radius = %d,\t Clear Circle :radius = %d" % (radius, clear_radius))
        if radius < max_radius:
            circle = circle_pixels(xc, yc, radius)
            color = colors[radius]

            # 衝突処理
            # Check collision and mix colors if needed
            # collision = set(circle1) & set(circle2)
            # for x, y in collision:
            #    draw_frame([(x, y)], [(color1[0] + color2[0]) // 2, (color1[1] + color2[1]) // 2, (color1[2] + color2[2]) // 2])

            draw_slave(circle, color)
            # print(f"Slave: {slave_pixels}")

            radius += 1

        # 描画している円の幅がCIRCLE_WIDTH以上になったら真ん中から消していく
        if radius > CIRCLE_WIDTH:
            clear_circle = circle_pixels(xc, yc, clear_radius)
            # 描画を消す
            draw_frame(clear_circle, [0, 0, 0])
            # print(f"Clear_Slave: {slave_pixels}")
            clear_radius += 1
        time.sleep(0.1)


def handle_command(command):
    # 受信したコマンドに応じて描画処理を実行する
    if command["type"] == "draw":
        x = command["x"]
        y = command["x"]
        colors = command["colors"]
        animation_slave_thread = threading.Thread(target=slave_pixels, args=(x, y, colors, max_radius,))
        animation_slave_thread.daemon = True  # メインが終われば終わる
        animation_slave_thread.start()
    elif command["type"] == "clear":
        clear_screen()


def get_client_id():
    """ユニークなクライアントIDを生成"""
    return f"Device_{socket.gethostname()}"


def listen_for_master_data(client_socket):
    """マスターからのデータを受信"""
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            try:
                received_data = json.loads(data.decode())
                print(f"Received from master: {received_data}")
                # 受信できたらデータの処理をする
                handle_command(received_data)
            except json.JSONDecodeError:
                print("Failed to decode data from master")
    except Exception as e:
        print(f"Error receiving from master: {e}")
    finally:
        client_socket.close()


def send_to_master(client_socket, data: dict):
    """任意のデータをマスターに送信"""
    try:
        client_socket.send(json.dumps(data).encode())
        print(f"Sent to master: {data}")
    except Exception as e:
        print(f"Failed to send to master: {e}")


def start_local_server(port=12345):
    # スレーブがコマンドを待機するローカルサーバー
    def server_loop():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("0.0.0.0", port))
            server_socket.listen()
            print(f"Local server listening on port {port}")
            while True:
                conn, _ = server_socket.accept()
                with conn:
                    data = b""
                    while True:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                    print(f"Received raw data: {data}")
                    try:
                        command = json.loads(data.decode('utf-8'))
                        print(f"Decoded command: {command}")
                        handle_command(command)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Raw data: {data}")

    server_thread = threading.Thread(target=server_loop, daemon=True)
    server_thread.start()


def setup_slave(master_ip, master_port, row, column):
    """スレーブをマスターと接続"""
    client_id = get_client_id()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((master_ip, master_port))
        print(f"Connected to master at {master_ip}:{master_port}")

        # 接続時に初期データを送信
        init_data = {
            "type": "init",
            "client_id": client_id,
            "position": {"row": row, "column": column}
        }
        send_to_master(client_socket, init_data)

        # マスターからのデータを受信するスレッドを開始
        listener_thread = threading.Thread(target=listen_for_master_data, args=(client_socket,))
        listener_thread.daemon = True
        listener_thread.start()

        # 任意のデータを送信する例
        while True:
            sensor_data = {
                "type": "sensor_data",
                "client_id": client_id,
                "position": {"row": row, "column": column},
                "data": {"temperature": 25, "humidity": 60}
            }
            send_to_master(client_socket, sensor_data)
            time.sleep(5)

    except Exception as e:
        print(f"Error setting up slave: {e}")
    except KeyboardInterrupt:
        print(f"Keyboard Interrupt")
    finally:
        clear_screen()
        client_socket.close()


if __name__ == '__main__':
    clear_screen()  # 初期化で消灯
    start_local_server(port=12345)  # ローカルサーバーを開始
    setup_slave(MASTER_IP, MASTER_PORT, SLAVE_ROWS, SLAVE_COLS)  # マスターに接続ing.Thread(target=server_loop, daemon=True)
    server_thread.start()


def setup_slave(master_ip, master_port, row, column):
    """スレーブをマスターと接続"""
    client_id = get_client_id()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((master_ip, master_port))
        print(f"Connected to master at {master_ip}:{master_port}")

        # 接続時に初期データを送信
        init_data = {
            "type": "init",
            "client_id": client_id,
            "position": {"row": row, "column": column}
        }
        send_to_master(client_socket, init_data)

        # マスターからのデータを受信するスレッドを開始
        listener_thread = threading.Thread(target=listen_for_master_data, args=(client_socket,))
        listener_thread.daemon = True
        listener_thread.start()

        # 任意のデータを送信する例
        while True:
            sensor_data = {
                "type": "sensor_data",
                "client_id": client_id,
                "position": {"row": row, "column": column},
                "data": {"temperature": 25, "humidity": 60}
            }
            send_to_master(client_socket, sensor_data)
            time.sleep(5)

    except Exception as e:
        print(f"Error setting up slave: {e}")
    except KeyboardInterrupt:
        print(f"Keyboard Interrupt")
    finally:
        clear_screen()
        client_socket.close()


if __name__ == '__main__':
    clear_screen()  # 初期化で消灯
    start_local_server(port=12345)  # ローカルサーバーを開始
    setup_slave(MASTER_IP, MASTER_PORT, SLAVE_ROWS, SLAVE_COLS)  # マスターに接続