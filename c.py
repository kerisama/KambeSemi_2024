import time

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