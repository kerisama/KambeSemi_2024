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

def draw_circle(strip,x_circle,y_circle,radius,color):
    x = 0
    y = radius
    d = 1 - radius

    while x <= y:
        # Draw points for each octant
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= x_circle + dx < MATRIX_WIDTH and 0 <= y_circle + dy < MATRIX_HEIGHT:
                strip.setPixelColor(zigzag_matrix(x_circle + dx, y_circle + dy), color)
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1

# Expand circle
# Expanding circle with tracked pixels for faster clearing
def expanding_circle(strip, max_radius, color, x_center, y_center, wait_ms=50):
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
                if 0 <= x_center + dx < MATRIX_WIDTH and 0 <= y_center + dy < MATRIX_HEIGHT:
                    pixel = zigzag_matrix(x_center + dx, y_center + dy)
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

# Mix two colors (average the RGB values)
def mix_colors(color1,color2):
    r = (color1 >> 16 & 0xFF + color2 >> 16 & 0xFF) // 2
    g = (color1 >> 8 & 0xFF + color2 >> 8 & 0xFF) // 2
    b = (color1 & 0xFF + color2 & 0xFF) // 2
    return Color(r,g,b)

# Detecting collision
def detect_collision(circle1,circle2):
    dx = circle1[0] - circle2[0]
    dy = circle1[1] - circle2[1]
    distance_squared = dx**2 + dy**2
    return distance_squared <= (circle1[2] + circle2[2]) ** 2

# Handling collision
def handle_collision(strip, circle1, circle2):
    pixels1 = circle_pixels(circle1[0],circle1[1],circle1[2])
    pixels2 = circle_pixels(circle2[0],circle2[1],circle2[2])

    overlapping_pixels = set(pixels1) & set(pixels2)

    for x, y in overlapping_pixels:
        pixel_index = zigzag_matrix(x,y)
        mix_color = mix_colors(pixels1[pixel_index],pixels2[pixel_index])
        strip.setPixelColor(pixel_index, mix_color)
    strip.show()
    time.sleep(0.5)

    for x,y in overlapping_pixels:
        pixel_index = zigzag_matrix(x,y)
        strip.setPixelColor(pixel_index, Color(0,0,0))
    strip.show()

# Circles
circles = []

# Generate circle pixels for a given center and radius
def circle_pixels(x_circle, y_circle, radius):
    x = 0
    y = radius
    d = 1 - radius
    pixels = []

    while x <= y:
        for dx, dy in [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]:
            if 0 <= x_circle + dx < MATRIX_WIDTH and 0 <= y_circle + dy < MATRIX_HEIGHT:
                pixels.append((x_circle + dx, y_circle + dy))
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1

    return pixels

def circle_generate():
    x_center,y_center = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
    color = Color(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
    circles.append([x_center,y_center,0,color])
    return x_center, y_center, color

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
            x_center, y_center, color = circle_generate()
            circles.append([x_center,y_center,0,color])

            # Expanding Circle Test
            # print('Expanding Circle')
            # expanding_circle(strip, 8, color, x_center, y_center, 100)

            for circle in circles:
                circle[2] += 1
                draw_circle(strip,circle[0],circle[1],circle[2],circle[3])

                for other_circle in circles:
                    if circle != other_circle and detect_collision(circle,other_circle):
                        handle_collision(strip,circle,other_circle)
                        circles.remove(circle)
                        circles.remove(other_circle)
                        break


            strip.show()
            time.sleep(0.1)


    except KeyboardInterrupt:
        if args.color:
            ColorWipe(strip,Color(0,0,0),10)