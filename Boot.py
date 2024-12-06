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
toggle_state = 0

""" マスターとスレーブの判別 (0をマスター、1をスレーブとする) """
Pi_status = 0


""" スレッドの管理 """
threads = {
    "single": None,
    "master": None,
    "slave": None,
}


""" 終了 """
def quitting():
    print("Shutting down...")
    os.system("sudo shutdown now")


def start_thread(name,target):
    """ スレッドの開始 or 再起動 """
    if threads[name] is None or not threads[name].is_alive():
        threads[name] = threading.Thread(target=target,daemon=True)
        threads[name].start()
        print(f"{name.capitalize()} Function Started!")
    else:
        print(f"{name.capitalize()} Function already Running.")


def stop_thread(name):
    """ スレッドの停止 """
    if threads[name] is not None and threads[name].is_alive():
        if name == "single":
            single.stop()
        elif name == "master":
            m_master.stop()
        elif name == "slave":
            m_slave.stop()
        threads[name].join()
        print(f"{name.capitalize()} Function Stopped.")


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

            if press_duration >= 3:
                # 3秒以上で複数機能
                if Pi_status == 0:     # マスター
                    stop_thread("single")
                    start_thread("master",m_master.run)
                else:   # スレーブ
                    stop_thread("single")
                    start_thread("slave",m_slave.run)

            elif press_duration >= 1:
                # 1秒以上で単体に戻す
                stop_thread("master")
                stop_thread("slave")
                start_thread("single",single.run)

            elif press_duration >= 5:
                quitting()      # 5秒以上押すとシャットダウン

            # elif press_duration >= 1:
            #     singlefunc()

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