import time

running = True

def main():
    time.sleep(1)
    print("B")

def run():
    global running
    running = True
    while running:
        main()

def stop():
    global running
    running = False
    print("Quitting...")

if __name__ == "__main__":
    main()