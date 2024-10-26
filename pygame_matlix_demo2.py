import pygame
import random
import math

# 中心から光が広がっていくやつ

# Pygameの初期設定
pygame.init()

# 画面サイズとLEDの定義
MATRIX_WIDTH = 32
MATRIX_HEIGHT = 32
LED_SIZE = 20
SCREEN_WIDTH = MATRIX_WIDTH * LED_SIZE
SCREEN_HEIGHT = MATRIX_HEIGHT * LED_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# 中央位置の計算
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# 光の輪を格納するリスト
lights = []


# 光の生成クラス
class Light:
    def __init__(self):
        # 光を中央に配置
        self.x = CENTER_X
        self.y = CENTER_Y
        # 光の色(ランダムなRGB)
        self.color = (random.randint(100,255),random.randint(100,255),random.randint(100,255))
        # 半径の初期化
        self.radius = 1
        # 拡大測度
        self.grouth_rate = random.uniform(1.0,3.0)

    def expand(self):
        # 半径を拡大
        self.radius += self.grouth_rate

    def draw(self):
        # 光の円描画
        pygame.draw.circle(screen,self.color,(self.x,self.y),int(self.radius),16)

    def is_outside_screen(self):
        # 円が範囲外に出たかどうか
        return self.radius > max(SCREEN_WIDTH,SCREEN_HEIGHT)

# メインループ
running = True
clock = pygame.time.Clock()

while running:
    screen.fill((255, 255, 255))  # 背景を白く

    # ランダムに新しい光を生成
    if len(lights) < 1:
        lights.append(Light())  #最大光数の制限

    # 生成された光を拡大＆描画
    for light in lights[:]:
        light.expand()
        light.draw()

        if light.is_outside_screen():
            lights.remove(light)

    pygame.display.flip()  # 画面を更新

    # イベント処理（終了処理）
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    clock.tick(60)  # FPS制御

pygame.quit()
