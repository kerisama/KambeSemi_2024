import RPi.GPIO as GPIO
import time

# GPIO ピンの設定
SWITCH_PIN = 20  # スイッチを接続するピン
GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # プルアップ設定
time.sleep(0.1)

# 機能の定義
def single_function():
    print("単数機能を実行中")

def multiple_function():
    print("複数機能を実行中")

# メインループ
while True:
    if GPIO.input(SWITCH_PIN) == GPIO.LOW:  # スイッチが押された場合
        single_function()
    else:  # スイッチが押されていない場合
        multiple_function()
    time.sleep(0.1) 

GPIO.cleanup()
