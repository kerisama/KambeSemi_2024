import socket
import json
from rpi_ws281x import PixelStrip, Color
import random
import time
import math
import numpy as np
import threading
from typing import Dict, Tuple

# LED configuration
LED_COUNT = 256
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_PER_PANEL = 16

# Matrix setup
MATRIX_WIDTH = 2  # Number of horizontal panels
MATRIX_HEIGHT = 2  # Number of vertical panels
MATRIX_GLOBAL_WIDTH = MATRIX_WIDTH * LED_PER_PANEL
MATRIX_GLOBAL_HEIGHT = MATRIX_HEIGHT * LED_PER_PANEL

# 円の幅
CIRCLE_WIDTH = 5

# 通信設定
PORT = 5000

# Initialize master LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()


class MultiClientServer:
    def __init__(self, port: int = 5000):
        self.host = '0.0.0.0'
        self.port = port
        self.clients: Dict[Tuple[int, int], socket.socket] = {}  # {(row, column): socket}

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Master server listening on port {self.port}")

        try:
            while True:
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.shutdown(server_socket)

    def handle_client(self, client_socket: socket.socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                try:
                    received_data = json.loads(data.decode())
                    if received_data["type"] == "init":
                        # クライアントの位置情報を登録
                        position = tuple(received_data["position"].values())  # (row, column)
                        self.clients[position] = client_socket
                        print(f"Registered client at position: {position}")

                    elif received_data["type"] == "sensor_data":
                        position = tuple(received_data["position"].values())
                        print(f"Received from {position}: {received_data}")

                except json.JSONDecodeError:
                    print("Failed to decode data from client")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.remove_client(client_socket)

    def send_to_position(self, row: int, column: int, data: dict):
        """特定の位置にデータを送信"""
        position = (row, column)
        if position in self.clients:
            try:
                self.clients[position].send(json.dumps(data).encode())
                print(f"Sent to {position}: {data}")
            except Exception as e:
                print(f"Failed to send to {position}: {e}")
        else:
            print(f"No client at position {position}")

    def broadcast(self, data: dict):
        """すべてのクライアントにデータをブロードキャスト"""
        for position, client_socket in list(self.clients.items()):
            try:
                client_socket.send(json.dumps(data).encode())
                print(f"Broadcasted to {position}: {data}")
            except Exception as e:
                print(f"Failed to broadcast to {position}: {e}")

    def remove_client(self, client_socket: socket.socket):
        """クライアントを削除"""
        for position, socket in list(self.clients.items()):
            if socket == client_socket:
                del self.clients[position]
                print(f"Removed client at position: {position}")
                break

    def shutdown(self, server_socket):
        """すべてのクライアントとサーバーソケットを閉じる"""
        for client_socket in self.clients.values():
            client_socket.close()
        server_socket.close()
        print("Server shutdown complete")


def zigzag_transform(x, y):
    if y % 2 == 1:  # Zigzag for odd rows
        x = LED_PER_PANEL - 1 - x
    return x, y


def clear_screen():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


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


def draw_frame(frame_pixels, color):
    # Draw a single frame of animation.
    # マスターの範囲内ならmaster_pixelsに、それ以外はslave_pixelsにする
    master_pixels = [p for p in frame_pixels if p[0] < LED_PER_PANEL and p[1] < LED_PER_PANEL]
    slave_pixels = [p for p in frame_pixels if p[0] >= LED_PER_PANEL or p[1] >= LED_PER_PANEL]

    # Draw master pixels
    for x, y in master_pixels:
        zigzag_x, zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

    # print(f"Master: {master_pixels}")
    

    return slave_pixels, color


def animate_circles(server):
    # max_radius = min(MATRIX_GLOBAL_WIDTH, MATRIX_GLOBAL_HEIGHT) // 2
    max_radius = 15

    # 円の中心を指定
    # xc1, yc1 = random.randint(0, MATRIX_GLOBAL_WIDTH - 1), random.randint(0, MATRIX_GLOBAL_HEIGHT - 1)
    # xc2, yc2 = random.randint(0, MATRIX_GLOBAL_WIDTH - 1), random.randint(0, MATRIX_GLOBAL_HEIGHT - 1)
    xc, yc = 15, 1

    radius = 0
    clear_radius = 0
    
    # 円の描画
    while True:
        if clear_radius == max_radius:
            break
        print("Draw Circle :radius = %d,\t Clear Circle :radius = %d" % (radius, clear_radius))
        if radius < max_radius:
            circle = circle_pixels(xc, yc, radius)
            color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]


            # 衝突処理
            # Check collision and mix colors if needed
            # collision = set(circle1) & set(circle2)
            # for x, y in collision:
            #    draw_frame([(x, y)], [(color1[0] + color2[0]) // 2, (color1[1] + color2[1]) // 2, (color1[2] + color2[2]) // 2])
            
            slave_pixels, color = draw_frame(circle, color)
            #print(f"Slave: {slave_pixels}")

            # スレーブに送信
            # slave_pixelsがあれば全スレーブに送信(broadcast)
            if len(slave_pixels):  # 円の描画を送信
                command = {"type": "draw", "coordinates": slave_pixels, "color": color}
                server.broadcast(command)
            radius += 1
        
        # 描画している円の幅がCIRCLE_WIDTH以上になったら真ん中から消していく
        if radius > CIRCLE_WIDTH:
            clear_circle = circle_pixels(xc,yc,clear_radius)
            # 描画を消す
            clear_slave_pixels, clear_color = draw_frame(clear_circle,[0,0,0])
            #print(f"Clear_Slave: {slave_pixels}")

            if len(slave_pixels):  # 円の削除を送信
                command = {"type": "draw", "coordinates": clear_slave_pixels, "color": [0, 0, 0]}
                server.broadcast(command)
            clear_radius += 1
        time.sleep(0.1)
    return server


if __name__ == '__main__':
    # 通信設定
    clear_screen()
    server = MultiClientServer()
    server_thread = threading.Thread(target=server.start_server)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        while True:
            # 円のアニメーション
            animate_circles(server)
    except KeyboardInterrupt:
        # 終了 (円の削除)
        clear_screen()
        command = {"type": "clear"}
        server.broadcast(command)
    finally:
        if hasattr(server, 'server_socket'):
            server.shutdown(server.server_socket)
        else:
            print("Server socket not found.")
