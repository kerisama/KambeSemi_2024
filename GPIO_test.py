import RPi.GPIO as GPIO
import time

# GPIOモードを設定
GPIO.setmode(GPIO.BCM)

# 使用するピンを指定
BUTTON_PIN = 3

# GPIOピンを入力モードに設定（プルアップ抵抗付き）
GPIO.setup(BUTTON_PIN, GPIO.IN)

# コールバック関数
def button_pressed(channel):
    print("Button was pressed!")

# イベントを登録
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_pressed, bouncetime=200)

try:
    print("Monitoring button presses...")
    while True:
        time.sleep(1)  # 無限ループで待機
except KeyboardInterrupt:
    print("Exiting program.")
finally:
    GPIO.cleanup()  # 終了時にGPIOをリセット
