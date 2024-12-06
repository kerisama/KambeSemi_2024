""" 起動直後 """
import RPi.GPIO as GPIO
import os
import time
import a
import b
import c


""" GPIO設定 """
BUTTON_PIN = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN,pull_up_down=GPIO.PUD_UP)

# トグル用フラグ
toggle_state = 0
STATUS = 0


def program_a():
    global toggle_state
    if toggle_state == 0:
        print("Start Program A")
        a.main()
        toggle_state = 1
    else:
        print("Stop Program A")
        toggle_state = 0

def program_b():
    global toggle_state
    if toggle_state == 0:
        print("Start Program B")
        b.main()
        toggle_state = 1
    else:
        print("Stop Program B")
        toggle_state = 0

def program_c():
    global toggle_state
    if toggle_state == 0:
        print("Start Program C")
        c.main()
        toggle_state = 1
    else:
        print("Stop Program C")
        toggle_state = 0

""" 終了 """
def quitting():
    print("Shutting down...")
    os.system("sudo shutdown now")


""" ボタンのプログラム """
def monitor_button():
    print("起動しました!")
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # ボタンが押されたとき
            start_time = time.time()  # 押し始めた時間を記録

            # ボタンを押している間の監視
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                pass  # ボタンが押されている間ループ

            press_duration = time.time() - start_time  # 押していた時間を計測

            if press_duration >= 5:
                quitting()  # 5秒以上ならシャットダウン
            elif press_duration >= 3:
                if STATUS == 0:
                    program_b()  # 3秒以上なら複数
                elif STATUS == 1:
                    program_c()
            elif press_duration >= 1:
                program_a()  # 1秒以上なら単体(?)


def main():
    try:
        print("ボタンを監視中... (CTRL+Cで終了)")
        monitor_button()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("終了しました")

if __name__ == "__main__":
    main()