import random
import time
import argparse
from rpi_ws281x import PixelStrip, Color

# Constants for LED matrix dimensions
MATRIX_WIDTH = 16  # Adjust based on your setup
MATRIX_HEIGHT = 16  # Adjust based on your setup

# LED setting
LED_COUNT = 256  # Adjust based on your setup
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_INVERT = False
LED_BRIGHTNESS = 255
LED_CHANNEL = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Helper functions
def zigzag_matrix(x, y):
    if y % 2 == 0:
        return y * MATRIX_WIDTH + x
    else:
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

def pixel_clear(strip, pixels):
    for pixel in pixels:
        strip.setPixelColor(pixel, Color(0, 0, 0))
    strip.show()

def mix_colors(color1, color2):
    r = (color1 >> 16 & 0xFF + color2 >> 16 & 0xFF) // 2
    g = (color1 >> 8 & 0xFF + color2 >> 8 & 0xFF) // 2
    b = (color1 & 0xFF + color2 & 0xFF) // 2
    return Color(r, g, b)

# Expanding circles with collisions
def expanding_circles(strip, max_radius, colors, num_circles, wait_ms=50):
    circles = []
    previous_pixels = []

    # Initialize circles with random positions
    for _ in range(num_circles):
        xc = random.randint(0, MATRIX_WIDTH - 1)
        yc = random.randint(0, MATRIX_HEIGHT - 1)
        color = random.choice(colors)
        circles.append({'xc': xc, 'yc': yc, 'radius': 0, 'color': color})

    while any(circle['radius'] <= max_radius for circle in circles):
        # Clear previous pixels
        if previous_pixels:
            pixel_clear(strip, previous_pixels)

        current_pixels = []
        overlap_pixels = {}

        # Draw all circles
        for circle in circles:
            if circle['radius'] > max_radius:
                continue

            xc, yc, radius, color = circle['xc'], circle['yc'], circle['radius'], circle['color']
            x = 0
            y = radius
            d = 1 - radius
            while x <= y:
                for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
                    if 0 <= xc + dx < MATRIX_WIDTH and 0 <= yc + dy < MATRIX_HEIGHT:
                        pixel = zigzag_matrix(xc + dx, yc + dy)
                        if pixel in current_pixels:
                            overlap_pixels[pixel] = mix_colors(strip.getPixelColor(pixel), color)
                        else:
                            strip.setPixelColor(pixel, color)
                            current_pixels.append(pixel)
                if d < 0:
                    d += 2 * x + 3
                else:
                    d += 2 * (x - y) + 5
                    y -= 1
                x += 1
            circle['radius'] += 1

        # Handle overlaps
        for pixel, overlap_color in overlap_pixels.items():
            strip.setPixelColor(pixel, overlap_color)
            current_pixels.remove(pixel)

        strip.show()
        previous_pixels = current_pixels
        time.sleep(wait_ms / 1000.0)

# Main program
if __name__ == '__main__':
    # Parser setting
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    print('Press Ctrl+C to quit')
    print('Expanding Circles with Collision Detection')
    if not args.clear:
        print('Use -c argument to clear LEDs on exit')

    try:
        while True:
            colors = [Color(255, 0, 0), Color(0, 255, 0), Color(0, 0, 255)]
            expanding_circles(strip, 8, colors, 3, 100)
            # Clear the LEDs after each cycle
            pixel_clear(strip, range(LED_COUNT))

    except KeyboardInterrupt:
        if args.clear:
            pixel_clear(strip, range(LED_COUNT))
