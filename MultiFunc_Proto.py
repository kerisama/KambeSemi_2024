from time import sleep
from rpi_ws281x import PixelStrip, Color
import argparse
import random

# マトリクス枚数
MATRIX_ROWS = 1     # 横
MATRIX_COLS = 2     # 縦

# マトリクス設定
MATRIX_WIDTH = 16 * MATRIX_ROWS
MATRIX_HEIGHT = 16 * MATRIX_COLS

# LED設定
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False
LED_CHANNEL = 0

# ジグザグ配線の修正
def zigzag_matrix(x, y):
    if y % 2 == 0:  # Even rows
        return y * MATRIX_WIDTH + x
    else:  # Odd rows
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

# カラーワイプ
def ColorWipe(strip,color,wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color)
        strip.show()
        (sleep(wait_ms/1000.0))

# LEDの消灯
def pixel_clear(strip, pixels):
    for pixel in pixels:
        strip.setPixelColor(pixel, Color(0, 0, 0))
    strip.show()

# 色を混ぜる
def mix_colors(color1, color2):
    r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
    r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
    r = (r1 + r2) // 2
    g = (g1 + g2) // 2
    b = (b1 + b2) // 2
    return Color(r, g, b)

# 円が内側から消えている
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
        sleep(wait_ms / 100000.0)

# Circle collision
def colliding_circles(strip, max_radius, xc1, yc1, xc2, yc2, color1, color2, wait_ms=50):

    # Track drawn pixels
    pixels_circle1 = []
    pixels_circle2 = []
    collisions = []

    for radius in range(max_radius + 1):
        # Draw first circle
        new_pixels_circle1 = []
        for x, y in circle_pixels(xc1, yc1, radius):
            # print(f"Pixel index for (x, y) = {x, y}: {zigzag_matrix(x, y)}")
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

        sleep(1)

        # Update circle pixels
        pixels_circle1.extend(new_pixels_circle1)
        pixels_circle2.extend(new_pixels_circle2)

        # Show the updated frame
        strip.show()
        sleep(wait_ms / 1000.0)

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

        # print(f"Circle pixels for center ({xc}, {yc}) and radius {radius}: {pixels}")

    return pixels

# Main programs
if __name__ == '__main__':
    # parser setting
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--color',action='store_true',help='clear the display on exit')
    args = parser.parse_args()

    max_radius = MATRIX_WIDTH // 2

    # LED setting
    strip = PixelStrip(LED_COUNT,LED_PIN,LED_FREQ_HZ,LED_DMA,LED_INVERT,LED_BRIGHTNESS,LED_CHANNEL)
    strip.begin()

    print('Press Ctrl+C to quit')
    if not args.color:
        print('Use -c argument to clear LEDs on exit')

    try:
        while True:
            # ランダムな位置に中心点を決める (デモ用)
            # サーボモータ&ToFセンサの値を用いて中心を決める
            xc1, yc1 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
            print(f"target1: ({xc1, yc1})")
            xc2, yc2 = random.randint(0, MATRIX_WIDTH - 1), random.randint(0, MATRIX_HEIGHT - 1)
            print(f"target2: ({xc2, yc2})")

            # ランダムな色
            color1 = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            color2 = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            # 円がぶつかったら色が変わって消える
            print('Colliding Circles')
            colliding_circles(strip, max_radius, xc1, yc1, xc2, yc2, color1, color2, wait_ms=50)

            ColorWipe(strip, Color(0, 0, 0), 10)


    except KeyboardInterrupt:
        if args.color:
            ColorWipe(strip,Color(0,0,0),10)