# main_program.py
import threading
import other_program

def main():
    print("Main program started.")
    thread = None  # サブプログラム用のスレッド
    while True:
        command = input("Enter 'run' to execute other program, 'stop' to stop it, or 'exit' to quit: ")
        if command == 'run':
            if thread is None or not thread.is_alive():
                thread = threading.Thread(target=other_program.run, daemon=True)
                thread.start()
                print("Other program started.")
            else:
                print("Other program is already running.")
        elif command == 'stop':
            if thread and thread.is_alive():
                other_program.stop()  # サブプログラムを停止させるフラグを設定
                thread.join()  # スレッドが終了するのを待つ
                print("Other program stopped.")
            else:
                print("No running program to stop.")
        elif command == 'exit':
            if thread and thread.is_alive():
                other_program.stop()
                thread.join()
            print("Exiting program.")
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
