import sys
import time

time.sleep(1)
try:
    for i in range(10):
        print("Program A")
        time.sleep(1)
except KeyboardInterrupt:
    print("Quit A")
    sys.exit()