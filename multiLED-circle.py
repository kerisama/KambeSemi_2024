"""
複数枚のマトリクスLEDを1枚のマトリクスLEDとして認識し、円の描画と衝突アニメーションを実行する
"""
import serial
from rpi_ws281x import PixelStrip, Color
import time
import math
import random
from typing import Tuple, List

# マトリクスLEDの設定
MATRIX_WIDTH = 16   # 1マトリクスの幅
MATRIX_HEIGHT = 16  # 1マトリクスの高さ

# マトリクス枚数
MATRIX_ROWS = 3     # 縦方向のマトリクス数
MATRIX_COLS = 4     # 横方向のマトリクス数

# 子機ラズパイの台数
Pi_Count = 11

# LED設定
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

class MatrixLEDController:
    def __init__(self, uart_ports: List[str]):
        # マトリクス設定
        self.MATRIX_ROWS = MATRIX_ROWS
        self.MATRIX_COLS = MATRIX_COLS
        self.MATRIX_WIDTH = MATRIX_WIDTH
        self.MATRIX_HEIGHT = MATRIX_HEIGHT
        self.TOTAL_WIDTH = self.MATRIX_WIDTH * self.MATRIX_COLS
        self.TOTAL_HEIGHT = self.MATRIX_HEIGHT * self.MATRIX_ROWS

        # デバイス初期化
        self.uart_connections = []
        for port in uart_ports:
            uart = serial.Serial(
                port=port,
                baudrate=115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            self.uart_connections.append(uart)

        # ローカルLEDストリップの初期化
        self.strip = PixelStrip(
            self.MATRIX_WIDTH * self.MATRIX_HEIGHT,
            LED_PIN,
            LED_FREQ_HZ,
            LED_DMA,
            LED_BRIGHTNESS,
            LED_INVERT,
            LED_CHANNEL
        )
        self.strip.begin()

    def coordinate_to_device(self, x: int, y: int) -> Tuple[int, int, int]:
        """グローバル座標(x,y)をデバイス番号と局所座標に変換"""
        matrix_x = x // self.MATRIX_WIDTH
        matrix_y = y // self.MATRIX_HEIGHT
        device_number = matrix_y * self.MATRIX_COLS + matrix_x

        # マトリクス内での相対座標
        local_x = x % self.MATRIX_WIDTH
        local_y = y % self.MATRIX_HEIGHT

        # マトリクス内でのLED番号（ジグザグパターン対応）
        if local_y % 2 == 0:
            local_position = local_y * self.MATRIX_WIDTH + local_x
        else:
            local_position = local_y * self.MATRIX_WIDTH + (self.MATRIX_WIDTH - 1 - local_x)

        return device_number, local_position, (local_x, local_y)

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """全体の座標系でピクセルの色を設定"""
        if 0 <= x < self.TOTAL_WIDTH and 0 <= y < self.TOTAL_HEIGHT:
            device_number, local_position, _ = self.coordinate_to_device(x, y)

            if device_number == 0:
                self.strip.setPixelColor(local_position, Color(*color))
            elif device_number <= len(self.uart_connections):
                # スレーブに通信
                command = f"LED:{local_position}:{color[0]}:{color[1]}:{color[2]}\n"
                self.uart_connections[device_number-1].write(command.encode())

    def show(self):
        """すべてのデバイスを更新する"""
        self.strip.show()
        for uart in self.uart_connections:
            # スレーブに通信
            uart.write(b"SHOW\n")

    def clear(self):
        """すべてのLEDをクリア"""
        for y in range(self.TOTAL_HEIGHT):
            for x in range(self.TOTAL_WIDTH):
                self.set_pixel(x, y, (0, 0, 0))
        self.show()

    def circle_pixels(self, xc: int, yc: int, radius: int):
        """指定された中心と半径で円のピクセルを生成"""
        x = 0
        y = radius
        d = 1 - radius
        pixels = []

        while x <= y:
            for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
                if 0 <= xc + dx < self.TOTAL_WIDTH and 0 <= yc + dy < self.TOTAL_HEIGHT:
                    pixels.append((xc + dx, yc + dy))

            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

        return pixels

    def mix_colors(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """2つの色を平均化"""
        return tuple((a + b) // 2 for a, b in zip(color1, color2))

    def colliding_circles(self, max_radius: int, xc1: int, yc1: int, xc2: int, yc2: int,
                           color1: Tuple[int, int, int], color2: Tuple[int, int, int]):
        """円の衝突アニメーション"""
        pixels_circle1 = []
        pixels_circle2 = []
        collisions = []

        for radius in range(max_radius + 1):
            # 最初の円を描画
            new_pixels_circle1 = []
            for x, y in self.circle_pixels(xc1, yc1, radius):
                pixel_color = color1
                if (x, y) in pixels_circle2:
                    collisions.append((x, y))
                    pixel_color = self.mix_colors(color1, color2)
                self.set_pixel(x, y, pixel_color)
                new_pixels_circle1.append((x, y))

            # 2番目の円を描画
            new_pixels_circle2 = []
            for x, y in self.circle_pixels(xc2, yc2, radius):
                pixel_color = color2
                if (x, y) in pixels_circle1:
                    collisions.append((x, y))
                    pixel_color = self.mix_colors(color1, color2)
                self.set_pixel(x, y, pixel_color)
                new_pixels_circle2.append((x, y))

            # 更新された円のピクセルを保存
            pixels_circle1.extend(new_pixels_circle1)
            pixels_circle2.extend(new_pixels_circle2)

            # 表示を更新
            self.show()
            time.sleep(0.05)  # アニメーション速度の調整

        # 衝突が発生した場合、円を削除
        if collisions:
            print("Collision detected! Removing circles.")
            self._delete_circle_with_center_out(pixels_circle1, (xc1, yc1))
            self._delete_circle_with_center_out(pixels_circle2, (xc2, yc2))

    def _delete_circle_with_center_out(self, circle_pixels: List[Tuple[int, int]], center: Tuple[int, int]):
        """中心から外に向かって円を消す"""
        # 中心からの距離に基づいてピクセルをソート
        distances = []
        cx, cy = center
        for x, y in circle_pixels:
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            distances.append((distance, (x, y)))

        # 距離でソートしたピクセルを消去
        for _, (x, y) in sorted(distances):
            self.set_pixel(x, y, (0, 0, 0))
            self.show()
            time.sleep(0.01)  # 消去の速度を調整

def main():
    print("Colliding Circles Demo")

    # 11台のスレーブデバイスのUARTポートリスト
    uart_ports = [f'/dev/ttyAMA{i}' for i in range(1, Pi_Count + 1)]

    # コントローラの初期化
    controller = MatrixLEDController(uart_ports)

    # 画面クリア
    controller.clear()

    try:
        while True:
            # ランダムな位置に中心点を決める
            max_radius = min(controller.TOTAL_WIDTH, controller.TOTAL_HEIGHT) // 2
            xc1, yc1 = random.randint(0, controller.TOTAL_WIDTH - 1), random.randint(0, controller.TOTAL_HEIGHT - 1)
            xc2, yc2 = random.randint(0, controller.TOTAL_WIDTH - 1), random.randint(0, controller.TOTAL_HEIGHT - 1)

            # ランダムな色
            color1 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            color2 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            # 円がぶつかったら色が変わって消える
            print(f'Colliding Circles: ({xc1}, {yc1}) vs ({xc2}, {yc2})')
            controller.colliding_circles(max_radius, xc1, yc1, xc2, yc2, color1, color2)

            # 短い遅延の後、再開
            controller.clear()
            time.sleep(1)

    except KeyboardInterrupt:
        controller.clear()
        print("\n Quitting...")

if __name__ == "__main__":
    main()