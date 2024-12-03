import socket
import json
from rpi_ws281x import PixelStrip, Color

# LED設定
LED_COUNT = 256
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

def clear_screen():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def draw_pixels(coordinates, color):
    for x, y in coordinates:
        index = y * 16 + x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

def handle_command(command):
    if command["type"] == "draw":
        draw_pixels(command["coordinates"], command["color"])
    elif command["type"] == "clear":
        clear_screen()

def start_server(port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen()
        print("スレーブが待機中...")
        while True:
            conn, _ = server_socket.accept()
            with conn:
                data = conn.recv(1024)
                if not data:
                    continue
                try:
                    command = json.loads(data.decode('utf-8'))
                    handle_command(command)
                except json.JSONDecodeError as e:
                    print(f"JSONデコードエラー: {e}")

if __name__ == '__main__':
    clear_screen()
    start_server()
