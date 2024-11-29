import socket
import time
import math
import colorsys
from typing import Tuple

# マトリクスLEDの設定
MATRIX_WIDTH = 16   # 1マトリクスの幅
MATRIX_HEIGHT = 16  # 1マトリクスの高さ

# マトリクス全体のサイズ (例: 1x2のスレーブ配置)
MATRIX_ROWS = 1
MATRIX_COLS = 2
TOTAL_WIDTH = MATRIX_WIDTH * MATRIX_COLS
TOTAL_HEIGHT = MATRIX_HEIGHT * MATRIX_ROWS

# スレーブデバイスのIPアドレスリスト
SLAVE_IPS = ["192.168.1.101", "192.168.1.102"]  # スレーブ1, スレーブ2のIPアドレス
UDP_PORT = 5005  # ポート番号

class MatrixLEDController:
    def __init__(self, slave_ips):
        self.slave_ips = slave_ips
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_to_slave(self, slave_index, message):
        """スレーブデバイスにメッセージを送信"""
        if 0 <= slave_index < len(self.slave_ips):
            self.sock.sendto(message.encode(), (self.slave_ips[slave_index], UDP_PORT))

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """全体の座標系でピクセルの色を設定"""
        if 0 <= x < TOTAL_WIDTH and 0 <= y < TOTAL_HEIGHT:
            slave_index = x // MATRIX_WIDTH
            local_x = x % MATRIX_WIDTH
            local_y = y

            # メッセージフォーマット: LED:x:y:r:g:b
            message = f"LED:{local_x}:{local_y}:{color[0]}:{color[1]}:{color[2]}"
            self.send_to_slave(slave_index, message)

    def show(self):
        """すべてのスレーブデバイスを更新"""
        for i in range(len(self.slave_ips)):
            self.send_to_slave(i, "SHOW")

    def clear(self):
        """すべてのLEDをクリア"""
        for y in range(TOTAL_HEIGHT):
            for x in range(TOTAL_WIDTH):
                self.set_pixel(x, y, (0, 0, 0))
        self.show()

    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """HSV色空間をRGB化"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def draw_rectangle(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int], fill: bool = True):
        """四角形を描画"""
        for i in range(width):
            for j in range(height):
                if fill or i == 0 or i == width - 1 or j == 0 or j == height - 1:
                    cur_x = x + i
                    cur_y = y + j
                    if (0 <= cur_x < TOTAL_WIDTH and 0 <= cur_y < TOTAL_HEIGHT):
                        self.set_pixel(cur_x, cur_y, color)

def main():
    print("Matrix LED Master Controller")

    # コントローラの初期化
    controller = MatrixLEDController(SLAVE_IPS)

    # アニメーションの初期パラメータ
    color = (255, 0, 0)  # 赤色の四角形
    square_size = 8      # 四角形のサイズ

    try:
        while True:
            # 四角形を描画
            controller.clear()
            controller.draw_rectangle(4, 4, square_size, square_size, color)
            controller.show()
            time.sleep(1)

    except KeyboardInterrupt:
        controller.clear()
        print("\nQuitting...")

if __name__ == "__main__":
    main()
