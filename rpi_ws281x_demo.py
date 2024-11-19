# Import necessary libraries
import time
from rpi_ws281x import PixelStrip, Color

# Constants
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16
LED_COUNT = MATRIX_WIDTH * MATRIX_HEIGHT  # Total number of LEDs
PIN = 18  # GPIO pin connected to the LEDs
BRIGHTNESS = 255

# Function to map matrix coordinates to the LED array index
def get_led_index(x, y):
    if y % 2 == 0:  # Even rows
        return y * MATRIX_WIDTH + x
    else:  # Odd rows (zigzag)
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)

# Function to draw a line between two points (e.g., Bresenham's line algorithm)
def draw_line(strip, x0, y0, x1, y1, color):
    # Bresenham's Line Algorithm (simplified for learning purposes)
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        strip.setPixelColor(get_led_index(x0, y0), color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy

# Function to draw a triangle
def draw_triangle(strip, vertices, color):
    # Unpack vertices
    (x1, y1), (x2, y2), (x3, y3) = vertices
    draw_line(strip, x1, y1, x2, y2, color)
    draw_line(strip, x2, y2, x3, y3, color)
    draw_line(strip, x3, y3, x1, y1, color)

# Main function
def main():
    # Initialize LED strip
    strip = PixelStrip(LED_COUNT, PIN, brightness=BRIGHTNESS)
    strip.begin()

    try:
        while True:
            strip.clear()  # Clear the LED matrix
            # Define triangle vertices
            vertices = [(3, 3), (12, 3), (7, 10)]
            # Draw the triangle
            draw_triangle(strip, vertices, Color(255, 0, 0))  # Red color
            strip.show()
            time.sleep(1)  # Pause for a moment
    except KeyboardInterrupt:
        # Clear all LEDs on exit
        strip.clear()
        strip.show()
