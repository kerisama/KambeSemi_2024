import sys
import time

def main():
    time.sleep(1)
    try:
        for i in range(5):
            print("Program B")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Quit B")
        sys.exit()

if __name__ == "__main__":
    main()