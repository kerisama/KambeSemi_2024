import random
import time
import math
from rpi_ws281x import PixelStrip,Color

# Matrix settings
LED_ROWS = 16
LED_COLS = 16

# LED matlix settings
LED_COUNT = LED_ROWS * LED_COLS     # LED Counts (16×16)
LED_PIN = 18                        # GPIO Settings
LED_FREQ_HZ = 800000                # Frequence
LED_DMA = 10                        # DMA Settings
LED_BRIGHTNESS = 10                 # Brightness
LED_INVERT = False                  # Invert LED

# LED Setting
strip = PixelStrip(
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_BRIGHTNESS,
    LED_INVERT
)
strip.begin()

# Functions of Force sensor (For demo)
def generate_random_pressure():
    return random.randint(10,980)

# Define circles parameter
def pressure_to_speed(pressure_value):
    # Define circles speed from pressure value
    speed = max(0.01, (980 - pressure_value) / 1000) # Strong pressure makes fast circle.
    return speed

# Convert Coordinates to LED index
def set_Pixel(x,y,color):
    index = y * LED_ROWS + x
    strip.setPixelColor(index,color)

# Draw Circle
def draw_circle(x,y,radius,color):
    for y in range(LED_COLS):
        for x in range(LED_ROWS):
            dist = math.sqrt((x - LED_ROWS/2)**2 + (y - LED_COLS/2)**2)
            if dist <= radius:
                set_Pixel(x,y,color)

# Generate Circles
def generate_circle():
    pressure_value = generate_random_pressure()     # Get pressure value
    speed = pressure_to_speed(pressure_value)       # Define speed from pressure
    radius = 1                                      # Radius setting (Getting louder)
    # x,y values is defined from locates of the object
    x = random.randint(0,15)                  # Generate x value random value(0~15)
    y = random.randint(0,15)                  # Generate y value random value(0~15)
    color = Color(random.randint(50,200),random.randint(50,200),random.randint(50,200)) # Color Setting
    return x,y,radius,color,speed

def expand_circle(x,y,radius,color,speed):
    if (radius < LED_ROWS // 2 or radius < LED_COLS // 2):
        radius = speed * 1.5
    else:
        color = Color(0,0,0)

    draw_circle(x,y,radius,color)

# Main Loop
try:
    while True:
        x,y,radius,speed,color = generate_circle()  # Generating Circle
        draw_circle(x,y,radius,color)               # Show Circle

        # Expanding Circle
        expand_circle(x,y,radius,color,speed)

        # Wait
        time.sleep(1)

# finally:
#     strip.show()

# Exit
except KeyboardInterrupt:
    strip.fill(Color(0,0,0))
    strip.show()