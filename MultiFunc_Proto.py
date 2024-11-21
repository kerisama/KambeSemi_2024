import time
from rpi_ws281x import PixelStrip, Color
import argparse
import math
import random
import keyboard     # Gキー降下ようライブラリ

# Matrix setting
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LED Setting
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

# Circle parameters
MAX_CIRCLES = 4
circles = []

# Define zigzag matrix
def zigzag_matrix(x, y):
    if y % 2 == 0:  # Even rows
        return y * MATRIX_WIDTH + x
    else:  # Odd rows
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

# Clear specific pixels
def pixel_clear(strip, pixels):
    for pixel in pixels:
        strip.setPixelColor(pixel, Color(0, 0, 0))
    strip.show()

# Draw circle without filling
def draw_circle(strip, xc, yc, radius, color):
    pixels = []
    x = 0
    y = radius
    d = 1 - radius
    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < MATRIX_WIDTH and 0 <= yc + dy < MATRIX_HEIGHT:
                pixel = zigzag_matrix(xc + dx, yc + dy)
                strip.setPixelColor(pixel, color)
                pixels.append(pixel)
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
    strip.show()
    return pixels

# Mix two colors (average the RGB values)
def mix_colors(color1, color2):
    r = ((color1 >> 16) & 0xFF + (color2 >> 16) & 0xFF) // 2
    g = ((color1 >> 8) & 0xFF + (color2 >> 8) & 0xFF) // 2
    b = (color1 & 0xFF + color2 & 0xFF) // 2
    return Color(r, g, b)

# Collision detection and color mixing
def handle_collisions(strip, active_circles):
    all_pixels = {}
    to_clear = set()

    for circle in active_circles:
        for pixel in circle["pixels"]:
            if pixel in all_pixels:
                # Collision detected, mix colors
                mixed_color = mix_colors(all_pixels[pixel], circle["color"])
                strip.setPixelColor(pixel, mixed_color)
                to_clear.add(pixel)
            else:
                all_pixels[pixel] = circle["color"]

    # Clear overlapping areas
    for pixel in to_clear:
        strip.setPixelColor(pixel, Color(0, 0, 0))
    strip.show()

# Main program
if __name__ == "__main__":
    # parser setting
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--color", action="store_true", help="clear the display on exit")
    args = parser.parse_args()

    # LED setting
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    print("Press Ctrl+C to quit")
    print("Press 'G' to create a circle. Maximum of 4 circles.")
    if not args.color:
        print("Use -c argument to clear LEDs on exit")

    try:
        while True:
            # Check for 'G' key press to add a circle
            if keyboard.is_pressed("g"):
                if len(circles) < MAX_CIRCLES:
                    xc = random.randint(0, MATRIX_WIDTH - 1)
                    yc = random.randint(0, MATRIX_HEIGHT - 1)
                    radius = random.randint(1, 8)
                    color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    pixels = draw_circle(strip, xc, yc, radius, color)
                    circles.append({"xc": xc, "yc": yc, "radius": radius, "color": color, "pixels": pixels})
                    time.sleep(0.3)  # Prevent multiple detections of a single key press

            # Handle collisions and remove cleared circles
            handle_collisions(strip, circles)
            circles = [circle for circle in circles if set(circle["pixels"]) & set(strip.getPixels())]

    except KeyboardInterrupt:
        if args.color:
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(0, 0, 0))
            strip.show()
