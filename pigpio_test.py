import pigpio
import time

# GPIOピンの設定
BUTTON_PIN = 3

# pigpioデーモンに接続
pi = pigpio.pi()
if not pi.connected:
    exit()

# GPIOを入力モードに設定
pi.set_mode(BUTTON_PIN, pigpio.INPUT)

# プルアップ抵抗を有効化
#pi.set_pull_up_down(BUTTON_PIN, pigpio.PUD_UP)

# コールバック関数
def button_callback(gpio, level, tick):
    print(f"Button pressed! GPIO: {gpio}, Level: {level}, Tick: {tick}")

# エッジ検出を設定（FALLINGエッジ）
cb = pi.callback(BUTTON_PIN, pigpio.FALLING_EDGE, button_callback)

try:
    print("Monitoring button presses...")
    while True:
        time.sleep(1)  # 無限ループで待機
except KeyboardInterrupt:
    print("Exiting program.")
finally:
    # コールバックを解除して終了
    cb.cancel()
    pi.stop()
