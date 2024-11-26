import time
from rpi_ws281x import PixelStrip, Color
import argparse
import random

# Matrix panels
MATRIX_ROWS = 1     # 横
MATRIX_COLS = 1     # 縦

# Matrix setting
MATRIX_WIDTH = 16 * MATRIX_ROWS
MATRIX_HEIGHT = 16 * MATRIX_COLS

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

# Color Wiping
def ColorWipe(strip,color,wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color)
        strip.show()
        time.sleep(wait_ms/1000.0)

# Clear specific pixels
def pixel_clear(strip, pixels):
    for pixel in pixels:
        strip.setPixelColor(pixel, Color(0, 0, 0))
    strip.show()

# Mix colors (example: average of two colors)
def mix_colors(color1, color2):
    r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
    r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
    r = (r1 + r2) // 2
    g = (g1 + g2) // 2
    b = (b1 + b2) // 2
    return Color(r, g, b)

# Delete a circle from the center outward
def delete_circle(strip, circle_pixels, center, wait_ms=1):
    # Calculate distance of each pixel from the center
    distances = []
    cx, cy = center
    for x, y in circle_pixels:
        distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        distances.append((distance, (x, y)))

    # Sort pixels by distance from center
    distances.sort()
    sorted_pixels = [pixel for _, pixel in distances]

    # Clear pixels in order of distance
    for x, y in sorted_pixels:
        pixel = zigzag_matrix(x, y)
        strip.setPixelColor(pixel, Color(0, 0, 0))
        strip.show()
        time.sleep(wait_ms / 100000.0)

# Circle collision
def colliding_circles(strip, max_radius, color1, color2, wait_ms=50):
    # Randomly decide the centers of two circles
    xc1, yc1 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
    xc2, yc2 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)

    # Track drawn pixels
    pixels_circle1 = []
    pixels_circle2 = []
    collisions = []

    for radius in range(max_radius + 1):
        # Draw first circle
        new_pixels_circle1 = []
        for x, y in circle_pixels(xc1, yc1, radius):
            pixel = zigzag_matrix(x, y)
            if (x, y) in pixels_circle2:  # Collision detected
                collisions.append((x, y))
                strip.setPixelColor(pixel, mix_colors(color1, color2))  # Change color to mixed color
            else:
                strip.setPixelColor(pixel, color1)
                new_pixels_circle1.append((x, y))

        # Draw second circle
        new_pixels_circle2 = []
        for x, y in circle_pixels(xc2, yc2, radius):
            pixel = zigzag_matrix(x, y)
            if (x, y) in pixels_circle1:  # Collision detected
                collisions.append((x, y))
                strip.setPixelColor(pixel, mix_colors(color1, color2))  # Change color to mixed color
            else:
                strip.setPixelColor(pixel, color2)
                new_pixels_circle2.append((x, y))

        # Update circle pixels
        pixels_circle1.extend(new_pixels_circle1)
        pixels_circle2.extend(new_pixels_circle2)

        # Show the updated frame
        strip.show()
        time.sleep(wait_ms / 1000.0)

    # Remove the circles with center-out animation if collision occurred
    if collisions:
        print("Collision detected! Removing circles.")
        delete_circle(strip, pixels_circle1, (xc1, yc1), wait_ms)
        delete_circle(strip, pixels_circle2, (xc2, yc2), wait_ms)

# Generate circle pixels for a given center and radius
def circle_pixels(xc, yc, radius):
    x = 0
    y = radius
    d = 1 - radius
    pixels = []

    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < MATRIX_WIDTH and 0 <= yc + dy < MATRIX_HEIGHT:
                pixels.append((xc + dx, yc + dy))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1

    return pixels

# Main programs
if __name__ == '__main__':
    # parser setting
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--color',action='store_true',help='clear the display on exit')
    args = parser.parse_args()

    # LED setting
    strip = PixelStrip(LED_COUNT,LED_PIN,LED_FREQ_HZ,LED_DMA,LED_INVERT,LED_BRIGHTNESS,LED_CHANNEL)
    strip.begin()

    print('Press Ctrl+C to quit')
    print('Expanding Circle')
    if not args.color:
        print('Use -c argument to clear LEDs on exit')

    try:
        while True:
            print('Colliding Circles')
            colliding_circles(strip, 8, Color(255, 0, 0), Color(0, 0, 255), wait_ms=50)

            # print('Expanding Circle')
            # expanding_circle(strip, 8, Color(0, 255, 0), 100)

            ColorWipe(strip, Color(0, 0, 0), 10)


    except KeyboardInterrupt:
        if args.color:
            ColorWipe(strip,Color(0,0,0),10)