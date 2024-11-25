"""
11台の子機用
親機の指示を受け取って動作する
"""
# スレーブデバイス用のコード
import serial
from rpi_ws281x import PixelStrip,Color
import time
from typing import Tuple, List

# Matrix setting
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LED Setting
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT    # LEDの数
LED_PIN = 18                                # GPIOピンの設定
LED_FREQ_HZ = 800000                        # 周波数の設定 (フレームレート)
LED_DMA = 10                                # DMA設定
LED_BRIGHTNESS = 10                         # 明るさ
LED_INVERT = False                          # 信号反転
LED_CHANNEL = 0                             # LEDチャンネル

class LEDSlave:
    def __init__(self):
        # マトリクスの設定
        self.MATRIX_WIDTH = MATRIX_WIDTH
        self.MATRIX_HEIGHT = MATRIX_HEIGHT

        # UARTの初期化
        self.uart = serial.Serial(
            port='/dev/ttyAMA0',
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

        # LEDマトリクスの初期化
        self.strip = PixelStrip(
            self.MATRIX_WIDTH * self.MATRIX_HEIGHT,
            LED_PIN,
            LED_FREQ_HZ,
            LED_DMA,
            LED_INVERT,
            LED_BRIGHTNESS,
            LED_CHANNEL,
            ws.WS2811_STRIP_GRB
        )
        self.strip.begin()

    def run(self):
        """コマンド待受ループ"""
        while True:
            if self.uart.in_waiting:
                command = self.uart.readline().decode().strip()

                if command.startswith("LED:"):
                    # LED制御コマンドの処理
                    _, pos, r, g, b = command.split(":")
                    pos, r, g, b = map(int, [pos, r, g, b])
                    self.strip.setPixelColor(pos, Color(r, g, b))

                elif command == "SHOW":
                    # 表示更新
                    self.strip.show()


if __name__ == "__main__":
    # スレーブデバイスとして実行
    slave = LEDSlave()
    slave.run()