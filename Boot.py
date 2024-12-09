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

""" トグル用フラグ """
# toggle_state = 0

""" マスターとスレーブの判別 (0をマスター、1をスレーブとする) """
Pi_status = 0


""" スレッドの管理 """
threads = {
    "single": None,
    "master": None,
    "slave": None,
}

instances = {
    "single": None,
    "master": None,
    "slave": None,
}


""" 終了 """
def quitting():
    stop_all_threads()
    print("Shutting down...")
    os.system("sudo shutdown now")


""" スレッドの停止 """
def stop_all_threads():
    for name, thread in threads.items():
        if thread is not None and thread.is_alive():
            instances[name].stop()
            thread.join()
            print(f"{name.capitalize()} Function Stopped")
        threads[name] = None
        instances[name] = None

def start_thread(name, cls):
    """ スレッドの開始または再起動 """
    if threads[name] is None or not threads[name].is_alive():
        instances[name] = cls()
        threads[name] = threading.Thread(target=instances[name].run, daemon=True)
        threads[name].start()
        print(f"{name.capitalize()} Function Started!")
    else:
        print(f"{name.capitalize()} Function already Running.")


def main():
    print("Booted!")
    print("Press Ctrl-C to quit...")

    # 初期状態で単体機能開始
    start_thread("single",single.run)

    # ボタンのループ
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # ボタンが押されたとき
            start_time = time.time()    # 押し始めた時間を記録

            # ボタンを押している間の監視
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                pass    # ボタンが押されている間ループ

            press_duration = time.time() - start_time   # 押していた時間を記録

            if press_duration >= 5:
                quitting()      # 5秒以上押すとシャットダウン

            elif press_duration >= 3:
                # 3秒以上で複数機能
                if Pi_status == 0:     # マスター
                    stop_all_threads()
                    start_thread("master",m_master.run)
                else:   # スレーブ
                    stop_all_threads()
                    start_thread("slave",m_slave.run)

            elif press_duration >= 1:
                # 1秒以上で単体に戻す
                stop_all_threads()
                start_thread("single",single.run)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Quit")
        GPIO.cleanup()

"""
単体、複数機能のコードに runningフラグを実装する必要あり
(例) 
# sample.py
import time

running = True

def run():
    global running
    running = True
    while running:
        print("Sample")
        time.sleep(1)

def stop():
    global running
    running = False
    print("Quitting...")
"""