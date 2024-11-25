"""
複数枚のマトリクスLEDを1枚のマトリクスLEDとして認識できないか?
11台のスレーブ(子機)ラズパイを用意し、1枚のマトリクスLEDとして認識させたい
巨大な四角形をマトリクスLEDに表示させたい
"""
# マスターデバイス用のコード
import serial
from rpi_ws281x import PixelStrip, Color
import time
from typing import Tuple,List

# Matrix setting
MATRIX_WIDTH = 16   # 1マトリクスの幅
MATRIX_HEIGHT = 16  # 1マトリクスの高さ

# Matrix Counts
MATRIX_ROWS = 1     # 縦方向のマトリクス数
MATRIX_COLS = 3     # 横方向のマトリクス数

# LED Setting
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
            ws.WS2811_STRIP_GRB
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
            device_number, local_position, _ = self.coordinate_to_device(x, y)

            if device_number == 0:
                # ローカルデバイス
                self.strip.setPixelColor(local_position, Color(*color))
            elif device_number < len(self.uart_connections) + 1:
                # リモートデバイス
                command = f"LED:{local_position}:{color[0]}:{color[1]}:{color[2]}\n"
                self.uart_connections[device_number - 1].write(command.encode())

        def show(self):
            """すべてのデバイスを更新"""
            self.strip.show()
            for uart in self.uart_connections:
                uart.write(b"SHOW\n")

        def clear(self):
            """すべてのLEDをクリア"""
            for y in range(self.TOTAL_HEIGHT):
                for x in range(self.TOTAL_WIDTH):
                    self.set_pixel(x, y, (0, 0, 0))
            self.show()

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

def main():
    # 11台のスレーブデバイスのUARTポートリスト
    uart_ports = [f'/dev/ttyAMA{i}' for i in range(11)]

    # コントローラの初期化
    controller = MatrixLEDController(uart_ports)

    # 画面クリア
    controller.clear()

    # 大きな四角形を描画
    # 全体の大きさは48×64ピクセル (16×3 = 48高さ, 16×4 = 64幅)
    border_width = 2  # 枠の太さ

    # 外枠を描画（塗りつぶしなし）
    controller.draw_rectangle(
        border_width,  # 左端からの余白
        border_width,  # 上端からの余白
        controller.TOTAL_WIDTH - (border_width * 2),  # 幅
        controller.TOTAL_HEIGHT - (border_width * 2),  # 高さ
        (255, 0, 0),  # 赤色
        fill=False
    )

    # 表示を更新
    controller.show()

if __name__ == "__main__":
    main()