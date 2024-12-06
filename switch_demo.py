import RPi.GPIO as GPIO
import time
import os

# GPIO設定
BUTTON_PIN = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# トグル用のフラグ
toggle_state = 0


def shutdown():
    print("シャットダウンします...")
    os.system("sudo shutdown now")


def print_toggle_message():
    global toggle_state
    if toggle_state == 0:
        print("メッセージ1: ボタンが3秒間押されました")
        toggle_state = 1
    else:
        print("メッセージ2: ボタンが3秒間押されました")
        toggle_state = 0


def monitor_button():
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # ボタンが押されたとき
            start_time = time.time()  # 押し始めた時間を記録

            # ボタンを押している間の監視
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                pass  # ボタンが押されている間ループ

            press_duration = time.time() - start_time  # 押していた時間を計測

            if press_duration >= 5:
                shutdown()  # 5秒以上ならシャットダウン
            elif press_duration >= 3:
                print_toggle_message()  # 3秒以上ならトグルで文字出力


try:
    print("ボタンを監視中... (CTRL+Cで終了)")
    monitor_button()
except KeyboardInterrupt:
    GPIO.cleanup()
    print("終了しました")

# gptコードだけどこれで3秒押したら何か起こすってやつと5秒押したらシャットダウンできた