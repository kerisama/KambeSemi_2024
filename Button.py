import RPi.GPIO as GPIO
import time
import os
import threading

""" ボタンのGPIO設定 """
BUTTON_PIN = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN,pull_up_down=GPIO.PUD_UP)

""" トグル用フラグ """
# toggle_state = 0

""" マスターとスレーブの判別 (0をマスター、1をスレーブとする) """
Pi_status = 0


# スレッド定義
threads = {
    "a": None,
    "b": None,
    "c": None,
}

# instances = {
#     "a": None,
#     "b": None,
#     "c": None,
# }


# クラス
class FuncA:
    def __init__(self):
        self.running = True

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

    def run(self):
        while self.running:
            print("Running B")
            time.sleep(1)

    def stop(self):
        self.running = False
        print("Stopping B")


# 関数
def func_c():
    running = True
    while running:
        print("Running C")
        time.sleep(1)
    print("Stopping C")


def stop_all_threads():
    for name, thread in threads.items():
        if thread is not None and thread.is_alive():
            # instances[name].stop()
            thread.join()
            print(f"{name.capitalize()} Function Stopped")
        threads[name] = None
        # instances[name] = None

def start_thread(name, target_func):
    """ スレッドの開始または再起動 """
    if threads[name] is None or not threads[name].is_alive():
        # instances[name] = cls()
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

"""
def func_a():
    def run():
        running = True
        while running:
            time.sleep(1)
            print("A")
    def stop():
        running = False
        print("Quitting A")

def func_b():
    def run():
        running = True
        while running:
            time.sleep(1)
            print("B")
    def stop():
        running = False
        print("Quitting B")
"""



def monitor_button():
    print("Monitoring Button Pressed")
    start_thread("a", FuncA)    # クラスの呼び出し

    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # ボタンが押されたとき
            print("Button Pressed")
            start_time = time.time()  # 押し始めた時間を記録

            # ボタンを押している間の監視
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                pass  # ボタンが押されている間ループ

            press_duration = time.time() - start_time  # 押していた時間を計測

            if press_duration >= 5:
                shutdown()  # 5秒以上ならシャットダウン
            elif press_duration >= 3:
                stop_all_threads()
                start_thread("c", func_c)   # 関数の呼び出し
            elif press_duration >= 3:
                stop_all_threads()
                start_thread("a", FuncA)

try:
    print("Press CTRL+C to quit")
    monitor_button()
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Quitting...")