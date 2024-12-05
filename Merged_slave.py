
import pigpio
import math
import VL53L0X
import socket
import json
import spidev
import time
import threading

# Communication settings
MASTER_IP = "192.168.10.65"
MASTER_PORT = 5000

# Sensor and hardware settings
SPI_BUS = spidev.SpiDev()
SPI_BUS.open(0, 0)
SPI_BUS.max_speed_hz = 1000000

SERVO_PIN = 23
pi = pigpio.pi()

tof = VL53L0X.VL53L0X()
tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

DEGREE_CYCLE = 1
DISPLAY_X = 160
DISPLAY_Y = 160
S_X = 15
S_Y = 5
DISTANCE_ERROR = 30

SLAVE_ROWS = 1
SLAVE_COLS = 1

def calculate_coordinates(distance, angle):
    rad = math.radians(angle)
    x = distance * math.cos(rad)
    y = distance * math.sin(rad)
    return x, y

def setup_connection():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((MASTER_IP, MASTER_PORT))
        init_message = {
            "type": "init",
            "position": {"row": SLAVE_ROWS, "column": SLAVE_COLS}
        }
        client_socket.send(json.dumps(init_message).encode())
        return client_socket
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def send_data(client_socket, x, y):
    try:
        data = {
            "type": "sensor_data",
            "position": {"row": SLAVE_ROWS, "column": SLAVE_COLS},
            "coordinates": {"x": x, "y": y}
        }
        client_socket.send(json.dumps(data).encode())
    except Exception as e:
        print(f"Data send error: {e}")

def scan_and_send(client_socket):
    for angle in range(0, 91, DEGREE_CYCLE):
        pi.set_servo_pulsewidth(SERVO_PIN, (angle / 180) * (2500 - 500) + 500)
        time.sleep(0.05)
        distance = tof.get_distance() - DISTANCE_ERROR
        if distance > 0:
            x, y = calculate_coordinates(distance, angle)
            send_data(client_socket, x, y)
            print(f"Sent coordinates: x={x}, y={y}")

if __name__ == "__main__":
    try:
        client_socket = setup_connection()
        if client_socket:
            while True:
                scan_and_send(client_socket)
                time.sleep(1)
    except KeyboardInterrupt:
        tof.stop_ranging()
        pi.stop()
        if client_socket:
            client_socket.close()
