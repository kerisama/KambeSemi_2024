import time
from rpi_ws281x import PixelStrip,Color
import argparse
import math
import random

# Matrix setting
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16

# LED Setting
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA =10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

# Define zigzag matrix
def zigzag_matrix(x,y):
    if y % 2 == 0:  # Even rows
        return y * MATRIX_WIDTH + x
    else :      # Odd rows
        return y * MATRIX_HEIGHT + (MATRIX_WIDTH - 1 - x)

# Color Wiping
def ColorWipe(strip,color,wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def pixel_clear(strip,pixels):
    for pixel in pixels:
        strip.setPixelColor(pixel,Color(0,0,0))
    strip.show()

# Draw line
def draw_line(strip,x0,y0,x1,y1,color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    while True:
        strip.setPixelColor(zigzag_matrix(x0,y0),color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy

# Draw triangle
def draw_triangle(strip,vertices,color):
    (x1,y1),(x2,y2),(x3,y3) = vertices
    draw_line(strip,x1,y1,x2,y2,color)
    draw_line(strip,x2,y2,x3,y3,color)
    draw_line(strip,x3,y3,x1,y1,color)

def draw_circle(strip,xc,yc,radius,color):
    x = 0
    y = radius
    d = 1 - radius

    while x <= y:
        # Draw points for each octant
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= xc + dx < MATRIX_WIDTH and 0 <= yc + dy < MATRIX_HEIGHT:
                strip.setPixelColor(zigzag_matrix(xc + dx, yc + dy), color)
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1

# Expand circle
# Expanding circle with tracked pixels for faster clearing
def expanding_circle(strip, max_radius, color, wait_ms=50):
    xc = random.randint(0, MATRIX_WIDTH - 1)
    yc = random.randint(0, MATRIX_HEIGHT - 1)
    previous_pixels = []

    for radius in range(max_radius + 1):
        # Clear previous pixels
        if previous_pixels:
            pixel_clear(strip, previous_pixels)

        # Draw new circle and keep track of pixels
        current_pixels = []
        x = 0
        y = radius
        d = 1 - radius
        while x <= y:
            for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
                if 0 <= xc + dx < MATRIX_WIDTH and 0 <= yc + dy < MATRIX_HEIGHT:
                    pixel = zigzag_matrix(xc + dx, yc + dy)
                    strip.setPixelColor(pixel, color)
                    current_pixels.append(pixel)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1
        strip.show()
        previous_pixels = current_pixels
        time.sleep(wait_ms / 1000.0)


# Main programs
if __name__ == '__main__':
    # parser setting
    parser =argparse.ArgumentParser()
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
            expanding_circle(strip, 8, Color(200, 0, 200), 100)
            strip.show()
            time.sleep(3)

            ColorWipe(strip,Color(0,0,0),10)

    except KeyboardInterrupt:
        if args.color:
            ColorWipe(strip,Color(0,0,0),10)