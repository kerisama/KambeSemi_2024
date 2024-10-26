import pygame
import random
import math

# 中心に光の玉が集まってくるやつ

# Pygameの初期設定
pygame.init()

# 画面サイズとLEDの定義
MATRIX_WIDTH = 32
MATRIX_HEIGHT = 32
LED_SIZE = 20
SCREEN_WIDTH = MATRIX_WIDTH * LED_SIZE
SCREEN_HEIGHT = MATRIX_HEIGHT * LED_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# 中央位置(ここを物を置かれた位置に置き換えていきたい)
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# LEDを格納するリスト
leds = []


# 光の生成クラス
class Light:
    def __init__(self):
        # ランダムな位置に生成
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        # 光の色 (ランダムなRGB)
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        # 移動速度
        self.speed = random.uniform(1.0, 3.0)

    # 光を中心に動かす
    def move_towards_center(self):
        # 中心までの方向ベクトルを計算
        dx = CENTER_X - self.x
        dy = CENTER_Y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # 距離に応じた正規化と速度計算
        if distance > 1:  # 中心に重なるまで動く
            self.x += dx / distance * self.speed
            self.y += dy / distance * self.speed

    def draw(self):
        # Pygameで光を描画
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), LED_SIZE)


# メインループ
running = True
clock = pygame.time.Clock()

while running:
    screen.fill((255, 255, 255))  # 背景を白く

    # ランダムに新しい光を生成する
    if len(leds) < 100:  # 最大光数を制限
        leds.append(Light())

    # 生成された光を移動・描画する
    for led in leds:
        led.move_towards_center()
        led.draw()

    pygame.display.flip()  # 画面を更新

    # イベント処理（終了処理）
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    clock.tick(60)  # FPS制御

pygame.quit()
