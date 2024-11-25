import serial
from rpi_ws281x import *
import time
import math

class LEDController:
    def __init__(self, led_count, uart_ports, matrix_width, matrix_height):
        self.led_count = led_count
        self.uart_ports = uart_ports
        self.uart_connections = []
        self.matrix_width = matrix_width
        self.matrix_height = matrix_height
        
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
        self.strip = Adafruit_NeoPixel(
            led_count,
            18,
            800000,
            10,
            False,
            255,
            0,
            ws.WS2811_STRIP_GRB
        )
        self.strip.begin()

    def xy_to_position(self, x, y):
        """
        x,y座標をLEDの位置に変換
        ジグザグ配列のマトリクスLEDに対応
        """
        if y % 2 == 0:
            pos = y * self.matrix_width + x
        else:
            pos = y * self.matrix_width + (self.matrix_width - 1 - x)
        return pos

    def set_pixel_color(self, position, color):
        """指定された位置のLEDの色を設定"""
        device_number = position // self.led_count
        local_position = position % self.led_count
        
        if device_number == 0:
            self.strip.setPixelColor(local_position, Color(*color))
        else:
            if device_number <= len(self.uart_connections):
                command = f"LED:{local_position}:{color[0]}:{color[1]}:{color[2]}\n"
                self.uart_connections[device_number-1].write(command.encode())

    def set_pixel_xy(self, x, y, color):
        """x,y座標でピクセルの色を設定"""
        if 0 <= x < self.matrix_width and 0 <= y < self.matrix_height:
            position = self.xy_to_position(x, y)
            self.set_pixel_color(position, color)

    def draw_line(self, x0, y0, x1, y1, color):
        """ブレゼンハムのアルゴリズムを使用して線を描画"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                self.set_pixel_xy(x, y, color)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                self.set_pixel_xy(x, y, color)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        self.set_pixel_xy(x, y, color)

    def draw_rectangle(self, x0, y0, width, height, color, fill=False):
        """四角形を描画（塗りつぶしオプション付き）"""
        if fill:
            for y in range(y0, y0 + height):
                for x in range(x0, x0 + width):
                    self.set_pixel_xy(x, y, color)
        else:
            self.draw_line(x0, y0, x0 + width - 1, y0, color)  # 上辺
            self.draw_line(x0, y0 + height - 1, x0 + width - 1, y0 + height - 1, color)  # 下辺
            self.draw_line(x0, y0, x0, y0 + height - 1, color)  # 左辺
            self.draw_line(x0 + width - 1, y0, x0 + width - 1, y0 + height - 1, color)  # 右辺

    def draw_circle(self, x0, y0, radius, color, fill=False):
        """円を描画（塗りつぶしオプション付き）"""
        def draw_circle_points(x, y, cx, cy, color):
            self.set_pixel_xy(cx + x, cy + y, color)
            self.set_pixel_xy(cx - x, cy + y, color)
            self.set_pixel_xy(cx + x, cy - y, color)
            self.set_pixel_xy(cx - x, cy - y, color)
            self.set_pixel_xy(cx + y, cy + x, color)
            self.set_pixel_xy(cx - y, cy + x, color)
            self.set_pixel_xy(cx + y, cy - x, color)
            self.set_pixel_xy(cx - y, cy - x, color)

        x = radius
        y = 0
        err = 0

        if fill:
            for cy in range(y0 - radius, y0 + radius + 1):
                for cx in range(x0 - radius, x0 + radius + 1):
                    if (cx - x0) * (cx - x0) + (cy - y0) * (cy - y0) <= radius * radius:
                        self.set_pixel_xy(cx, cy, color)
        else:
            while x >= y:
                draw_circle_points(x, y, x0, y0, color)
                y += 1
                err += 1 + 2 * y
                if 2 * (err - x) + 1 > 0:
                    x -= 1
                    err += 1 - 2 * x

    def draw_triangle(self, x0, y0, x1, y1, x2, y2, color, fill=False):
        """三角形を描画（塗りつぶしオプション付き）"""
        if fill:
            # 三角形の塗りつぶし（単純な実装）
            min_x = min(x0, x1, x2)
            max_x = max(x0, x1, x2)
            min_y = min(y0, y1, y2)
            max_y = max(y0, y1, y2)

            def point_in_triangle(px, py):
                def sign(x1, y1, x2, y2, x3, y3):
                    return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)

                d1 = sign(px, py, x0, y0, x1, y1)
                d2 = sign(px, py, x1, y1, x2, y2)
                d3 = sign(px, py, x2, y2, x0, y0)

                has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
                has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

                return not (has_neg and has_pos)

            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    if point_in_triangle(x, y):
                        self.set_pixel_xy(x, y, color)
        else:
            # 三角形の輪郭を描画
            self.draw_line(x0, y0, x1, y1, color)
            self.draw_line(x1, y1, x2, y2, color)
            self.draw_line(x2, y2, x0, y0, color)

    def show(self):
        """すべてのデバイスに表示命令を送信"""
        self.strip.show()
        for uart in self.uart_connections:
            uart.write(b"SHOW\n")

    def clear(self):
        """すべてのLEDをオフにする"""
        for y in range(self.matrix_height):
            for x in range(self.matrix_width):
                self.set_pixel_xy(x, y, (0,0,0))
        self.show()

# 使用例
if __name__ == "__main__":
    # マトリクスの設定
    MATRIX_WIDTH = 8
    MATRIX_HEIGHT = 8
    LEDS_PER_DEVICE = MATRIX_WIDTH * MATRIX_HEIGHT
    uart_ports = ['/dev/ttyAMA0', '/dev/ttyAMA1']
    
    controller = LEDController(LEDS_PER_DEVICE, uart_ports, MATRIX_WIDTH, MATRIX_HEIGHT)
    
    # 図形描画のデモ
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    
    # すべてのLEDをクリア
    controller.clear()
    
    # 四角形を描画
    controller.draw_rectangle(1, 1, 6, 6, RED)
    controller.show()
    time.sleep(2)
    
    # 円を描画
    controller.clear()
    controller.draw_circle(3, 3, 3, BLUE)
    controller.show()
    time.sleep(2)
    
    # 三角形を描画
    controller.clear()
    controller.draw_triangle(3, 1, 1, 6, 6, 6, GREEN)
    controller.show()
    time.sleep(2)
    
    # 線を描画
    controller.clear()
    controller.draw_line(0, 0, 7, 7, WHITE)
    controller.show()
    time.sleep(2)
    
    # クリア
    controller.clear()
