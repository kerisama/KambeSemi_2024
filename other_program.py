# other_program.py
import time

running = True  # サブプログラムを制御するフラグ

def run():
    global running
    running = True
    timer = 1
    print("Other program running. Press Ctrl+C to stop.")
    while running:
        print(f"time={timer}")
        timer += 1
        time.sleep(1)

def stop():
    global running
    running = False
