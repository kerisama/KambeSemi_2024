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

# Mix two colors (average the RGB values)
def mix_colors(color1,color2):
    r = 200
    g = 200
    b = 200
    return Color(r,g,b)

# Circle collision
def colliding_circles(strip, max_radius, color1, color2, wait_ms=50):
    # ランダムに2つの円の中心を決定
    xc1, yc1 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
    xc2, yc2 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)

    # 描画済みピクセルを追跡する辞書 (ピクセル位置 -> 色)
    pixels = {}

    for radius in range(max_radius + 1):
        # 描画するためのピクセルリストを保持
        new_pixels = {}

        # 1つ目の円を描画
        for x, y in circle_pixels(xc1, yc1, radius):
            pixel = zigzag_matrix(x, y)
            if pixel in pixels:  # 他の円と衝突
                mixed_color = mix_colors(pixels[pixel], color1)
                strip.setPixelColor(pixel, mixed_color)
                del pixels[pixel]  # 重なったピクセルは削除して消える
            else:
                strip.setPixelColor(pixel, color1)
                new_pixels[pixel] = color1

        # 2つ目の円を描画
        for x, y in circle_pixels(xc2, yc2, radius):
            pixel = zigzag_matrix(x, y)
            if pixel in pixels:  # 他の円と衝突
                mixed_color = mix_colors(pixels[pixel], color2)
                strip.setPixelColor(pixel, mixed_color)
                del pixels[pixel]  # 重なったピクセルは削除して消える
            else:
                strip.setPixelColor(pixel, color2)
                new_pixels[pixel] = color2

        # 現在のピクセル情報を更新
        pixels.update(new_pixels)
        strip.show()
        time.sleep(wait_ms / 1000.0)

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