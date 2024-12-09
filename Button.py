import RPi.GPIO as GPIO
import time
import os
import threading

""" ボタンのGPIO設定 """
BUTTON_PIN = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # PUD_UPの場合

""" トグル用フラグ """
toggle_state = 0

# スレッド定義
threads = {
    "a": None,
    "b": None,
    "c": None,
}


# クラス
class FuncA:
    def __init__(self):
        self.running = True
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while self.running:
            print("Running A")
            time.sleep(1)

    def stop(self):
        self.running = False
        print("Stopping A")


class FuncB:
    def __init__(self):
        self.running = True
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while self.running:
            print("Running B")
            time.sleep(1)

    def stop(self):
        self.running = False
        print("Stopping B")


def func_c():
    global toggle_state
    if toggle_state == 0:
        toggle_state = 1
        running = True
    else:
        running = False
        toggle_state = 0
        print("Stopping C")
    while running:
        print("Running C")
        time.sleep(1)


def stop_all_threads():
    global threads
    for name, thread in threads.items():
        if thread is not None and thread.is_alive():
            thread.join()
            print(f"{name.capitalize()} Function Stopped")
        threads[name] = None


def start_thread(name, target_func):
    """ スレッドの開始または再起動 """
    global threads
    if threads[name] is None or not threads[name].is_alive():
        threads[name] = threading.Thread(target=target_func, daemon=True)
        threads[name].start()
        print(f"{name.capitalize()} Function Started!")
    else:
        print(f"{name.capitalize()} Function already Running.")


def shutdown():
    print("Shutting down...")
    stop_all_threads()
    GPIO.cleanup()
    os.system("sudo shutdown now")


def monitor_button():
    global toggle_state
    print("Monitoring Button Pressed")
    start_thread("a", FuncA)  # 初期クラス起動

    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # ボタンが押されたとき
            print("Button Pressed")
            start_time = time.time()

            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                pass  # ボタンが押されている間ループ

            press_duration = time.time() - start_time

            if press_duration >= 5:  # 5秒以上
                shutdown()
            elif 3 <= press_duration < 5:  # 3～5秒
                stop_all_threads()
                start_thread("c", func_c)
            elif press_duration < 3:  # 3秒未満
                stop_all_threads()
                start_thread("a", FuncA)


try:
    print("Press CTRL+C to quit")
    monitor_button()
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Quitting...")
