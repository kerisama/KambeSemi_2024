"""
複数枚のマトリクスLEDを1枚のマトリクスLEDとして認識できないか?
11台のスレーブ(子機)ラズパイを用意し、1枚のマトリクスLEDとして認識させたい
巨大な四角形をマトリクスLEDに表示させたい
"""
# マスターデバイス用のコード
import serial
from rpi_ws281x import PixelStrip, Color
import time
import math
import colorsys
from typing import Tuple,List

# 子機ラズパイの台数
Pi_Count = 11

# マトリクスLEDの設定
MATRIX_WIDTH = 16   # 1マトリクスの幅
MATRIX_HEIGHT = 16  # 1マトリクスの高さ

# マトリクス枚数
MATRIX_ROWS = 3     # 縦方向のマトリクス数
MATRIX_COLS = 4     # 横方向のマトリクス数

# LED設定
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT    # LEDの数
LED_PIN = 18                                # GPIOピンの設定
LED_FREQ_HZ = 800000                        # 周波数の設定 (フレームレート)
LED_DMA = 10                                # DMA設定
LED_BRIGHTNESS = 10                         # 明るさ
LED_INVERT = False                          # 信号反転
LED_CHANNEL = 0                             # LEDチャンネル

class MatrixLEDController:
    def __init__(self, uart_ports: List[str]):
        # マトリクス設定
        self.MATRIX_ROWS = MATRIX_ROWS    # 縦方向のマトリクス数
        self.MATRIX_COLS = MATRIX_COLS    # 横方向のマトリクス数
        self.MATRIX_WIDTH = MATRIX_WIDTH    # 1マトリクスの幅
        self.MATRIX_HEIGHT = MATRIX_HEIGHT  # 1マトリクスの高さ
        self.TOTAL_WIDTH = self.MATRIX_WIDTH * self.MATRIX_COLS     # 全体の幅
        self.TOTAL_HEIGHT = self.MATRIX_HEIGHT * self.MATRIX_ROWS   # 全体の高さ

        # デバイス初期化
        self.uart_connections = []
        # UARTの初期化
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
            LED_CHANNEL,
            # ws.WS2811_STRIP_GRB
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
            elif device_number == len(self.uart_connections) + 1:
                command = f"LED:{local_position}:{color[0]}:{color[1]}:{color[2]}\n"
                self.uart_connections[device_number-1].write(command.encode())

    def show(self):
        """すべてのデバイスを更新する"""
        self.strip.show()
        for uart in self.uart_connections:
            uart.write(b"SHOW\n")

    def clear(self):
        """すべてのLEDをクリア"""
        for y in range(self.TOTAL_HEIGHT):
            for x in range(self.TOTAL_WIDTH):
                self.set_pixel(x, y, (0, 0, 0))
        self.show()

    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """HSV色空間をRGB化"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def draw_rectangle(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int],
                       fill: bool = True):
        """四角形を描画"""
        for i in range(width):
            for j in range(height):
                if fill or i == 0 or i == width - 1 or j == 0 or j == height - 1:
                    cur_x = x + i
                    cur_y = y + j
                    if (0 <= cur_x < self.TOTAL_WIDTH and
                            0 <= cur_y < self.TOTAL_HEIGHT):
                        self.set_pixel(cur_x, cur_y, color)

    def rotate_point(self, x: int, y: int, cx: int, cy: int, angle_red: float) -> Tuple[int,int]:
        cos_a = math.cos(angle_red)
        sin_a = math.sin(angle_red)

        # 中心を原点に移動する
        dx = x - cx
        dy = y - cy

        # 回転させる
        rx = dx * cos_a + dy * sin_a
        ry = dx * sin_a + dy * cos_a

        return (int(rx * cx), int(ry * cy))

    """虹色の正方形を描画する"""
    def draw_rotating_rainbow_square(self, size: int, angle: float):
        # 中心点
        center_x = self.TOTAL_WIDTH // 2
        center_y = self.TOTAL_HEIGHT // 2

        # 正方形の原点 (中心からの相対座標)
        half_size = size //2
        square_points = [
            (-half_size, -half_size),
            (half_size, -half_size),
            (half_size, half_size),
            (-half_size, half_size),
        ]

        # 回転後の原点計算
        rotated_points = [
            self.rotate_point(x + center_x, y + center_y, center_x, center_y, angle)
            for x, y in square_points
        ]

        # 各辺を描画する
        for i in range(4):
            start = rotated_points[i]
            end = rotated_points[(i + 1) % 4]

            dx = abs(end[0] - start[0])
            dy = abs(end[1] - start[1])
            x, y = start

            steep = dy > dx
            if steep:
                x, y = y, x
                dx, dy = dy, dx
                start = (start[1], start[0])
                end = (end[1], end[0])

            if start[0] > end[0]:
                x, end_x = end[0], start[0]
                y = end[1]
                step_y = -1 if end[1] > start[1] else 1
            else:
                x, end_x = start[0], end[0]
                y = start[1]
                ster_y = 1 if end[1] > start[1] else -1

            error = dx // 2

            # 変に沿って虹色を描画する
            for px in range(x, end_x + 1):
                # 現在の位置に基づいて色を計算
                hue = (i / 4 + px / self.TOTAL_WIDTH) % 1.0
                color = self.hsv_to_rgb(hue, 1.0, 1.0)

                if steep:
                    self.set_pixel(y,px,color)
                else:
                    self.set_pixel(px,y,color)

                error -= dy
                if error < 0:
                    y += step_y
                    error += dx


def main():
    print("Rotating Rainbow Square Demo")

    # 11台のスレーブデバイスのUARTポートリスト
    uart_ports = [f'/dev/ttyAMA{i}' for i in range(Pi_Count)]
    # コントローラの初期化
    controller = MatrixLEDController(uart_ports)

    # アニメーションの初期パラメータ
    square_size = min(controller.TOTAL_WIDTH, controller.TOTAL_HEIGHT)  # 四角の大きさ
    angle = 0   # 角度
    rotation_speed = 0.05   # 速度 (ラジアン/フレーム)

    # 画面クリア
    controller.clear()

    try:
        """普通の四角形の描画テスト"""
        # controller.draw_rectangle(controller.TOTAL_WIDTH - 2, controller.TOTAL_HEIGHT - 2, square_size, square_size, (0, 255, 0))

        """虹色の回転する四角形の描画テスト"""
        while True:
            controller.clear()  # 画面クリア
            controller.draw_rotating_rainbow_square(square_size,angle)  # 虹色の四角を描画
            controller.show()   # 表示

            angle = (angle + rotation_speed) % (2 * math.pi)
            time.sleep(0.05)    # 少し待つ

    except KeyboardInterrupt:
        controller.clear()
        print("\n Quitting...")

if __name__ == "__main__":
    main()