"""
MultiFunc_Protoとマージしてみたもの
もしマスター・スレーブ通信が成功したらこれも試したい
"""

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

    # スレーブにデータ送信
    def send_to_slave(self, slave_index, message):
        """スレーブデバイスにメッセージを送信"""
        if 0 <= slave_index < len(self.slave_ips):
            self.sock.sendto(message.encode(), (self.slave_ips[slave_index], UDP_PORT))

    # ピクセル表示
    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """全体の座標系でピクセルの色を設定"""
        if 0 <= x < TOTAL_WIDTH and 0 <= y < TOTAL_HEIGHT:
            slave_index = x // MATRIX_WIDTH
            local_x = x % MATRIX_WIDTH
            local_y = y

            # メッセージフォーマット: LED:x:y:r:g:b
            message = f"LED:{local_x}:{local_y}:{color[0]}:{color[1]}:{color[2]}"
            self.send_to_slave(slave_index, message)

    # 表示
    def show(self):
        """すべてのスレーブデバイスを更新"""
        for i in range(len(self.slave_ips)):
            self.send_to_slave(i, "SHOW")

    # クリア
    def clear(self):
        """すべてのLEDをクリア"""
        for y in range(TOTAL_HEIGHT):
            for x in range(TOTAL_WIDTH):
                self.set_pixel(x, y, (0, 0, 0))
        self.show()


def circle_pixels(xc, yc, radius):
    """与えられた中心と半径の円のピクセルを計算"""
    x = 0
    y = radius
    d = 1 - radius
    pixels = []

    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < TOTAL_WIDTH and 0 <= yc + dy < TOTAL_HEIGHT:
                pixels.append((xc + dx, yc + dy))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    return pixels


def colliding_circles(controller, max_radius, xc1, yc1, xc2, yc2, color1, color2, wait_ms=50):
    """円を描画し、衝突処理を行う"""
    pixels_circle1 = []
    pixels_circle2 = []
    collisions = []

    for radius in range(max_radius + 1):
        new_pixels_circle1 = []
        # 1つめ
        for x, y in circle_pixels(xc1, yc1, radius):
            if (x, y) in pixels_circle2:
                collisions.append((x, y))
                controller.set_pixel(x, y, (
                    (color1[0] + color2[0]) // 2,
                    (color1[1] + color2[1]) // 2,
                    (color1[2] + color2[2]) // 2
                ))
            else:
                controller.set_pixel(x, y, color1)
                new_pixels_circle1.append((x, y))

        new_pixels_circle2 = []
        # 2つめ
        for x, y in circle_pixels(xc2, yc2, radius):
            if (x, y) in pixels_circle1:
                collisions.append((x, y))
                controller.set_pixel(x, y, (
                    (color1[0] + color2[0]) // 2,
                    (color1[1] + color2[1]) // 2,
                    (color1[2] + color2[2]) // 2
                ))
            else:
                controller.set_pixel(x, y, color2)
                new_pixels_circle2.append((x, y))

        controller.show()
        time.sleep(wait_ms / 1000.0)
        pixels_circle1.extend(new_pixels_circle1)
        pixels_circle2.extend(new_pixels_circle2)

    for x, y in collisions:
        controller.set_pixel(x, y, (0, 0, 0))
    controller.show()

    # 色を混ぜる (仮)
    def mix_color(self, color1:Tuple[int,int,int], color2:Tuple[int,int,int]):
        r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
        r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
        r = (r1 + r2) // 2
        g = (g1 + g2) // 2
        b = (b1 + b2) // 2
        return Tuple[r, g, b]


def main():
    print("Matrix LED Master Controller")

    # コントローラの初期化
    controller = MatrixLEDController(SLAVE_IPS)

    # アニメーションの初期パラメータ
    color1 = (255, 0, 0)    # 色の設定(ランダムにする)
    color2 = (0, 255, 0)    # 色の設定(ランダムにする)

    max_radius = TOTAL_WIDTH // 2      # 半径の最大サイズ

    # 円の中心設定
    # センサの情報から極座標変換したものを中心とする
    xc1, yc1 = 10, 10   # 円1の中心
    xc2, yc2 = 20, 20   # 円2の中心

    try:
        while True:
            controller.clear()
            # 丸を描画
            colliding_circles(controller, max_radius, xc1, yc1, xc2, yc2, color1, color2)
            controller.show()
            time.sleep(1)

    except KeyboardInterrupt:
        controller.clear()
        print("\nQuitting...")

if __name__ == "__main__":
    main()
