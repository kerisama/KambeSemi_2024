import time
import random
from rpi_ws281x import PixelStrip, Color
import math

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
        return y * MATRIX_HEIGHT + (MATRIX_WIDTH - 1 - x)

# Clear the matrix
def clear_matrix(strip):
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# Move a point toward a target
def move_point_toward_target(strip, x, y, target_x, target_y, color, speed=0.05):
    while x != target_x or y != target_y:
        # Draw current position
        strip.setPixelColor(zigzag_matrix(x, y), color)
        strip.show()
        time.sleep(speed)

        # Clear the current position
        strip.setPixelColor(zigzag_matrix(x, y), Color(0, 0, 0))

        # Calculate direction
        dx = target_x - x
        dy = target_y - y
        if abs(dx) > abs(dy):
            x += 1 if dx > 0 else -1
        else:
            y += 1 if dy > 0 else -1

    # Draw the final position
    strip.setPixelColor(zigzag_matrix(x, y), color)
    strip.show()

# Main program
if __name__ == "__main__":
    # LED setting
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    try:
        while True:
            # Randomly generate multiple starting points and their colors
            points = []
            for _ in range(10):  # Number of points
                x = random.randint(0, MATRIX_WIDTH - 1)
                y = random.randint(0, MATRIX_HEIGHT - 1)
                color = Color(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                points.append((x, y, color))

            # Choose a random target point
            target_x = random.randint(0, MATRIX_WIDTH - 1)
            target_y = random.randint(0, MATRIX_HEIGHT - 1)

            # Move each point toward the target
            for x, y, color in points:
                move_point_toward_target(strip, x, y, target_x, target_y, color)

            # Pause before resetting
            time.sleep(2)

            # Clear the matrix
            clear_matrix(strip)

    except KeyboardInterrupt:
        # Clear on exit
        clear_matrix(strip)
