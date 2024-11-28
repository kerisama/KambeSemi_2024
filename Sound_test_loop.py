import subprocess
import time

heavy = 30 #圧力センサ
music = None #mp3ファイル

if 10 < heavy < 50:
    music = 'sample1.mp3'
elif 50 <= heavy < 150:
    music = 'sample2.mp3'
else:
    music = None

if music:
    while heavy > 10:
        process = subprocess.Popen(['mpg321', music])
        process.wait() 

    process.terminate()

