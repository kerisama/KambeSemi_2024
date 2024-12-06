""" 起動直後 """
import os
import singlecomplete3 as single        # 単体機能
import MultiFunc_master as m_master     # 複数機能 (マスター)
import MultiFunc_slave as m_slave       # 複数機能 (スレーブ)

""" 単体機能 """
def singlefunc():
    single.main()

""" 複数機能 (マスター) """
def multifunc_master():
    m_master.main()

""" 複数機能 (スレーブ) """
def multifunc_slave():
    m_slave.main()

def main():
    # ボタンの機能をここに
    print("main")

if __name__ == "__main__":
    main()