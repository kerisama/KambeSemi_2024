import socket
import json
from rpi_ws281x import PixelStrip, Color
import random
import time
import math

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
MATRIX_HEIGHT = 1  # Number of vertical panels
MATRIX_GLOBAL_WIDTH = MATRIX_WIDTH * LED_PER_PANEL
MATRIX_GLOBAL_HEIGHT = MATRIX_HEIGHT * LED_PER_PANEL

# Communication setup
SLAVE_IPS = ['192.168.10.61', '192.168.10.62']  # Add more as needed
PORT = 12345

# Initialize master LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()


def zigzag_transform(x, y):
    if y % 2 == 1:  # Zigzag for odd rows
        x = LED_PER_PANEL - 1 - x
    return x, y


def clear_screen():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


def send_command(command, ip_list):
    for ip in ip_list:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, PORT))
                client_socket.sendall(json.dumps(command).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send to {ip}: {e}")


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
    """Draw a single frame of animation."""
    master_pixels = [p for p in frame_pixels if p[0] < LED_PER_PANEL and p[1] < LED_PER_PANEL]
    slave_pixels = [[] for _ in SLAVE_IPS]

    # Allocate pixels to master or appropriate slave
    for p in frame_pixels:
        panel_x = p[0] // LED_PER_PANEL
        panel_y = p[1] // LED_PER_PANEL
        if panel_x == 0 and panel_y == 0:
            continue
        index = panel_y * MATRIX_WIDTH + panel_x - 1
        if index >= 0 and index < len(slave_pixels):  # Ensure valid slave index
            slave_pixels[index].append((p[0] % LED_PER_PANEL, p[1] % LED_PER_PANEL))

    # Remove duplicates from each slave's coordinates
    for i in range(len(slave_pixels)):
        slave_pixels[i] = list(set(slave_pixels[i]))

    # Draw master pixels
    for x, y in master_pixels:
        zigzag_x, zigzag_y = zigzag_transform(x, y)
        index = zigzag_y * LED_PER_PANEL + zigzag_x
        strip.setPixelColor(index, Color(color[0], color[1], color[2]))
    strip.show()

    # Send slave commands
    for i, ip in enumerate(SLAVE_IPS):
        if slave_pixels[i]:
            command = {"type": "draw", "coordinates": slave_pixels[i], "color": color}
            send_command(command, [ip])

    print(f"Master: {master_pixels}")
    for i, slave in enumerate(slave_pixels):
        print(f"Slave {i}: {slave}")

def animate_circles():
    max_radius = min(MATRIX_GLOBAL_WIDTH, MATRIX_GLOBAL_HEIGHT) // 2
    xc1, yc1 = random.randint(0, MATRIX_GLOBAL_WIDTH - 1), random.randint(0, MATRIX_GLOBAL_HEIGHT - 1)
    xc2, yc2 = random.randint(0, MATRIX_GLOBAL_WIDTH - 1), random.randint(0, MATRIX_GLOBAL_HEIGHT - 1)
    color1 = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
    color2 = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

    for radius in range(max_radius):
        circle1 = circle_pixels(xc1, yc1, radius)
        circle2 = circle_pixels(xc2, yc2, radius)

        # Check collision and mix colors if needed
        collision = set(circle1) & set(circle2)
        for x, y in collision:
            draw_frame([(x, y)], [(color1[0] + color2[0]) // 2, (color1[1] + color2[1]) // 2, (color1[2] + color2[2]) // 2])

        draw_frame(circle1, color1)
        draw_frame(circle2, color2)
        time.sleep(0.1)

    # Clear circles from the center outwards
    def clear_from_center(circle_pixels, center):
        cx, cy = center
        sorted_pixels = sorted(circle_pixels, key=lambda p: math.dist([cx, cy], p))
        for pixel in sorted_pixels:
            draw_frame([pixel], [0, 0, 0])
            time.sleep(0.01)

    clear_from_center(circle1, (xc1, yc1))
    clear_from_center(circle2, (xc2, yc2))


if __name__ == '__main__':
    clear_screen()
    try:
        while True:
            animate_circles()
    except KeyboardInterrupt:
        clear_screen()
