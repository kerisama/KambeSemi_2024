from pygame.locals import *
import pygame
import sys
import subprocess

pygame.init()  # Pygameを初期化
screen = pygame.display.set_mode((400, 330))  # 画面を作成
pygame.display.set_caption("keyboard event")  # タイトルを作成

while True:
    screen.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:  # キーを押したとき
            # ESCキーならスクリプトを終了
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

            else:
                # print("押されたキー = " + pygame.key.name(event.key))
                if event.key ==K_a:
                    command = ["python","a.py"]
                    proc = subprocess.Popen(command)
                    print("呼び出し中...")
                    proc.communicate()
                elif event.key ==K_b:
                    command = ["python", "b.py"]
                    proc = subprocess.Popen(command)
                    print("呼び出し中...")
                    proc.communicate()
        pygame.display.update()