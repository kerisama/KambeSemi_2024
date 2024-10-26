import pygame
import math
import time

# 初期設定
pygame.init()

# 画面サイズ
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

# 色
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# 輪っかのリスト
circles = []


# 輪っかのクラス
class Circle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.color = BLUE
        self.start_time = time.time()
        self.collided = False

    def update(self):
        # 半径を広げる
        self.radius += 2

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius, 2)

    def check_collision(self, other):
        # 他の輪っかとの距離を計算
        dist = math.hypot(self.x - other.x, self.y - other.y)
        return dist < self.radius + other.radius


# メインループ
running = True
while running:
    screen.fill(WHITE)

    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # マウスクリックで輪っかを作成
            x, y = pygame.mouse.get_pos()
            circles.append(Circle(x, y))

    # 輪っかの更新と描画
    for circle in circles:
        circle.update()
        circle.draw(screen)

    # 輪っか同士の衝突判定
    for i, circle in enumerate(circles):
        for other_circle in circles[i + 1:]:
            if circle.check_collision(other_circle):
                # 衝突が発生した場合の色の変更
                circle.color = RED
                other_circle.color = RED
                circle.collided = True
                other_circle.collided = True

    # 衝突後3秒経過したら消去
    circles = [c for c in circles if not (c.collided and time.time() - c.start_time > 1.5)]

    # 画面更新
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
