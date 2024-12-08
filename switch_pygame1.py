import pygame
import threading
import time
import os
from a import A
from b import B
from c import C
from d import D

""" トグル用フラグ """
Pi_status = 1

""" スレッドの管理 """
threads = {
    "a": None,
    "b": None,
    "c": None,
    "d": None,
}

instances = {
    "a": None,
    "b": None,
    "c": None,
    "d": None,
}

""" Stop All Threads """
def stop_all_threads():
    for name, thread in threads.items():
        if thread is not None and thread.is_alive():
            instances[name].stop()
            thread.join()
            print(f"{name.capitalize()} Function Stopped")
        threads[name] = None
        instances[name] = None

def start_thread(name, cls):
    """ スレッドの開始 or 再起動 """
    if threads[name] is None or not threads[name].is_alive():
        instances[name] = cls()
        threads[name] = threading.Thread(target=instances[name].run, daemon=True)
        threads[name].start()
        print(f"{name.capitalize()} Function Started!")
    else:
        print(f"{name.capitalize()} Function already Running.")

def stop_thread(name):
    """ スレッドの停止 """
    if threads[name] is not None and threads[name].is_alive():
        instances[name].stop()
        threads[name].join()
        print(f"{name.capitalize()} Function Stopped.")
        threads[name] = None
        instances[name] = None

def main():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Key Control Example")

    print("Booted!")
    print("Press 'q' to quit...")

    # 初期状態でAを起動
    start_thread("a", A)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:  # '1'キーでAに切り替え
                    print("Key '1' pressed: Switching to A")
                    stop_all_threads()
                    start_thread("a", A)

                elif event.key == pygame.K_2:  # '2'キーでBまたはCに切り替え
                    print("Key '2' pressed: Switching to B or C")
                    stop_all_threads()
                    if Pi_status == 0:  # マスター
                        start_thread("b", B)
                    else:  # スレーブ
                        start_thread("c", C)

                elif event.key == pygame.K_3:  # '3'キーでDに切り替え
                    print("Key '3' pressed: Switching to D")
                    stop_all_threads()
                    start_thread("d", D)

                elif event.key == pygame.K_q:  # 'q'キーでプログラム終了
                    print("Key 'q' pressed: Quitting")
                    stop_all_threads()
                    running = False

        pygame.display.flip()
        time.sleep(0.1)

    pygame.quit()
    print("Exited cleanly")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Quit")
