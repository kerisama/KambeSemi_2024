import time
from rpi_ws281x import PixelStrip, Color
import argparse
import random

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

# Draw an expanding circle
def expanding_circle(strip, circles, max_radius, color, wait_ms=50):
    xc = random.randint(0, MATRIX_WIDTH - 1)
    yc = random.randint(0, MATRIX_HEIGHT - 1)
    radius = 0
    pixels = []

    while radius <= max_radius:
        # Draw circle outline
        new_pixels = []
        x = 0
        y = radius
        d = 1 - radius
        while x <= y:
            for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
                if 0 <= xc + dx < MATRIX_WIDTH and 0 <= yc + dy < MATRIX_HEIGHT:
                    pixel = zigzag_matrix(xc + dx, yc + dy)
                    new_pixels.append(pixel)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

        # Check for collisions
        collided_pixels = check_collisions(circles, new_pixels)
        if collided_pixels:
            # Mix colors for collisions
            for pixel in collided_pixels:
                strip.setPixelColor(pixel, mix_colors(strip.getPixelColor(pixel), color))
            strip.show()
            return  # Stop expanding if a collision occurs

        # Update and display the new circle
        pixel_clear(strip, pixels)  # Clear previous circle
        for pixel in new_pixels:
            strip.setPixelColor(pixel, color)
        strip.show()
        pixels = new_pixels
        circles.append(new_pixels)  # Add to active circles
        radius += 1
        time.sleep(wait_ms / 1000.0)

# Check for collisions
def check_collisions(circles, new_pixels):
    collided_pixels = []
    for circle in circles:
        for pixel in new_pixels:
            if pixel in circle:
                collided_pixels.append(pixel)
    return collided_pixels

# Mix two colors
def mix_colors(color1, color2):
    r = (color1 >> 16 & 0xFF + color2 >> 16 & 0xFF) // 2
    g = (color1 >> 8 & 0xFF + color2 >> 8 & 0xFF) // 2
    b = (color1 & 0xFF + color2 & 0xFF) // 2
    return Color(r, g, b)

# Main programs
if __name__ == '__main__':
    # Parser setting
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--color', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # LED setting
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    print('Press Ctrl+C to quit')
    print('Expanding Circle with Collision Detection')
    if not args.color:
        print('Use -c argument to clear LEDs on exit')

    try:
        circles = []  # List to store active circles
        while True:
            if len(circles) < 4:  # Allow up to 4 circles
                expanding_circle(strip, circles, 8, Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), 100)
            else:
                time.sleep(0.1)  # Wait if the maximum number of circles is reached
    except KeyboardInterrupt:
        if args.color:
            pixel_clear(strip, range(LED_COUNT))
