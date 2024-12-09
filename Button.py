import threading
import time
import RPi.GPIO as GPIO

""" ボタンのGPIO設定 """
BUTTON_PIN = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

""" スレッド管理用変数 """
current_thread = None
stop_event = threading.Event()

class ManagedThread:
    def __init__(self, target):
        self.target = target
        self.thread = None

    def start(self):
        global stop_event
        stop_event.clear()
        self.thread = threading.Thread(target=self.target, daemon=True)
        self.thread.start()

    def stop(self):
        global stop_event
        stop_event.set()
        if self.thread is not None:
            self.thread.join()

# 各スレッドの処理
def func_a():
    global stop_event
    print("Starting A")
    while not stop_event.is_set():
        print("Running A")
        time.sleep(1)
    print("Stopping A")

def func_b():
    global stop_event
    print("Starting B")
    while not stop_event.is_set():
        print("Running B")
        time.sleep(1)
    print("Stopping B")

class func_c:
    def __init__(self):
        self.running = True
        threading.Thread(target=self.run,daemon=True).start()

    def run(self):
        while self.running and not stop_event.is_set():
            print("Running C")
            time.sleep(1)

    def stop(self):
        self.running = False
        print("Stopping C")

def stop_current_thread():
    global current_thread
    if current_thread is not None:
        current_thread.stop()
        current_thread = None

def start_new_thread(target_func):
    global current_thread
    stop_current_thread()  # 現在のスレッドを停止
    if callable(target_func):
        current_thread = ManagedThread(target_func)
        current_thread.start()
    elif isinstance(target_func,type):
        current_thread = target_func()

def monitor_button():
    print("Monitoring Button")
    start_new_thread(func_a)

    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # ボタンが押されたとき
            print("Button Pressed")
            start_time = time.time()

            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                pass

            press_duration = time.time() - start_time

            if press_duration >= 5:  # 5秒以上
                print("Shutting Down")
                stop_current_thread()
                GPIO.cleanup()
                break
            elif press_duration >= 3:  # 3秒以上
                print("Switching to Function C")
                start_new_thread(func_c)
            elif press_duration < 3:  # 3秒未満
                print("Switching to Function B")
                start_new_thread(func_b)

try:
    print("Press CTRL+C to quit")
    monitor_button()
except KeyboardInterrupt:
    print("Exiting Program")
    stop_current_thread()
    GPIO.cleanup()
