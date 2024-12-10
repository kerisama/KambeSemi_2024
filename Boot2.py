""" 起動直後 """
import RPi.GPIO as GPIO
import time
import os
import threading
import singlecomplete3 as single        # 単体機能
import MultiFunc_master as m_master     # 複数機能 (マスター)
import MultiFunc_slave as m_slave       # 複数機能 (スレーブ)

""" ボタンのGPIO設定 """
BUTTON_PIN = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN,pull_up_down=GPIO.PUD_UP)

""" スレッド管理用変数 """
current_thread = None
stop_event = threading.Event()
isSingleMode = False

""" マスターとスレーブの判別 (0をマスター、1をスレーブとする) """
Pi_status = 0


""" スレッド管理用クラス """
class ManagedThread:
    def __init__(self,target):
        self.target = target
        self.thread = None

    def start(self):
        global stop_event
        stop_event.clear()
        self.thread = threading.Thread(target=self.target,daemon=True)
        self.thread.start()

    def stop(self):
        global stop_event
        stop_event.set()
        if self.thread is not None:
            self.thread.join()


""" 終了 """
def quitting():
    print("Shutting down...")
    os.system("sudo shutdown now")


""" 各機能の関数 """
# 単体機能
def single_function():
    global stop_event
    print("Start Single function")
    while not stop_event.is_set():
        print("tmp")    # ダミー
        time.sleep(1)
    print("Stop Single function")

# 複数機能 (マスター)
def multi_function():
    global stop_event
    print("Start Multi function (Master)")
    while not stop_event.is_set():
        print("tmp")  # ダミー
        time.sleep(1)
    print("Stop Multi function (Master)")

# 複数機能　(スレーブ)
"""
def multi_func_slave():
    global stop_event
    print("Start Multi function (Slave)")
    while not stop_event.is_set():
        print("tmp")  # ダミー
        time.sleep(1)
    print("Stop Multi function (Slave)")
"""


def boot():
    global isSingleMode,current_thread
    print("Booted!")
    print("Press Ctrl-C to quit...")

    # 初期スレッドの起動
    current_thread = ManagedThread(target=single_function if isSingleMode else multi_function)
    current_thread.start()

    # ボタンのループ
    while True:
        # # 単体機能であるかどうか
        # if isSingleMode:
        #     isSingleMode = single_function()
        # else:
        #     isSingleMode = multi_function()

        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # ボタンが押されたとき
            print("Button pressed")     # ボタン降下(デバッグ用)
            start_time = time.time()    # 押し始めた時間を記録

            # ボタンを押している間の監視
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                pass    # ボタンが押されている間ループ

            press_duration = time.time() - start_time   # 押していた時間を記録

            if press_duration >= 5:
                # 5秒以上押すとシャットダウン
                current_thread.stop()
                quitting()

            elif press_duration >= 3:
                # 3秒以上で複数機能
                isSingleMode = False
                current_thread.stop()
                current_thread = ManagedThread(target=multi_function)
                current_thread.start()

            elif press_duration >= 1:
                # 1秒以上で単体に戻す
                isSingleMode = True
                current_thread.stop()
                current_thread = ManagedThread(target=single_function)
                current_thread.start()


if __name__ == "__main__":
    try:
        boot()
    except KeyboardInterrupt:
        print("Quit")
        GPIO.cleanup()