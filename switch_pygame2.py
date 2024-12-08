import pygame
import threading
import time

""" 各クラス定義 """
class A:
    def __init__(self):
        self.running = True

    def main(self):
        time.sleep(1)
        print("A is running...")

    def run(self):
        self.running = True
        while self.running:
            self.main()

    def stop(self):
        self.running = False
        print("A is stopping...")

class B:
    def __init__(self):
        self.running = True

    def main(self):
        time.sleep(1)
        print("B is running...")

    def run(self):
        self.running = True
        while self.running:
            self.main()

    def stop(self):
        self.running = False
        print("B is stopping...")

class C:
    def __init__(self):
        self.running = True

    def main(self):
        time.sleep(1)
        print("C is running...")

    def run(self):
        self.running = True
        while self.running:
            self.main()

    def stop(self):
        self.running = False
        print("C is stopping...")

class D:
    def __init__(self):
        self.running = True

    def main(self):
        time.sleep(1)
        print("D is running...")

    def run(self):
        self.running = True
        while self.running:
            self.main()

    def stop(self):
        self.running = False
        print("D is stopping...")

""" スレッド管理用辞書 """
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

""" スレッドの停止 """
def stop_all_threads():
    for name, thread in threads.items():
        if thread is not None and thread.is_alive():
            instances[name].stop()
            thread.join()
            print(f"{name.capitalize()} Function Stopped")
        threads[name] = None
        instances[name] = None

def start_thread(name, cls):
    """ スレッドの開始または再起動 """
    if threads[name] is None or not threads[name].is_alive():
        instances[name] = cls()
        threads[name] = threading.Thread(target=instances[name].run, daemon=True)
        threads[name].start()
        print(f"{name.capitalize()} Function Started!")
    else:
        print(f"{name.capitalize()} Function already Running.")

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
                    start_thread("b", B)

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
