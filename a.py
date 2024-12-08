import time

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
