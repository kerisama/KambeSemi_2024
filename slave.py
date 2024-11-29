import socket
from rpi_ws281x import PixelStrip, Color

# マトリクスLEDの設定
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

# UDP設定
UDP_IP = "0.0.0.0"  # すべてのインターフェースで待機
UDP_PORT = 5005

class SlaveController:
    def __init__(self):
        self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_BRIGHTNESS, LED_INVERT, LED_CHANNEL)
        self.strip.begin()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        if 0 <= x < MATRIX_WIDTH and 0 <= y < MATRIX_HEIGHT:
            led_index = y * MATRIX_WIDTH + (x if y % 2 == 0 else (MATRIX_WIDTH - 1 - x))
            self.strip.setPixelColor(led_index, Color(color[0], color[1], color[2]))

    def show(self):
        self.strip.show()

    def clear(self):
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def listen(self):
        print("Slave listening for UDP packets...")
        while True:
            data, addr = self.sock.recvfrom(1024)
            message = data.decode().strip()
            if message.startswith("LED:"):
                _, x, y, r, g, b = message.split(":")
                self.set_pixel(int(x), int(y), (int(r), int(g), int(b)))
            elif message == "SHOW":
                self.show()
            elif message == "CLEAR":
                self.clear()

def main():
    controller = SlaveController()
    try:
        controller.listen()
    except KeyboardInterrupt:
        controller.clear()
        print("\nQuitting...")

if __name__ == "__main__":
    main()
