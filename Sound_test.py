
#coding:utf-8

import RPi.GPIO as GPIO
import time
import math

pin = 21   #任意のピン番号
a0=27.500   #低いラの音

#n番目の音階の周波数を返す
def onkai(n):
    return a0*math.pow(math.pow(2,1/12),n)

#それぞれの音の周波数を定義
DO=onkai(27)
RE=onkai(29)
MI=onkai(31)
SO=onkai(34)

#メロディとリズムを配列に
mery_merody=[MI,RE,DO,RE,MI,MI,MI,RE,RE,RE,MI,SO,SO,MI,RE,DO,RE,MI,MI,MI,RE,RE,MI,RE,DO]
mery_rhythm=[0.9,0.3,0.6,0.6,0.6,0.6,1.2,0.6,0.6,1.2,0.6,0.6,1.2,0.9,0.3,0.6,0.6,0.6,0.6,1.2,0.6,0.6,0.9,0.3,1.8]

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin,GPIO.OUT,initial=GPIO.LOW)

p = GPIO.PWM(pin,1)
p.start(50)

#なぜか最初の方は変な音がするので適当に鳴らす
p.ChangeFrequency(2)
time.sleep(2)

#配列の通りに鳴らす
for i, oto in enumerate(mery_merody):
    p.start(50)
    p.ChangeFrequency(oto)
    time.sleep(mery_rhythm[i])
    p.stop()
    time.sleep(0.03)

p.stop()
GPIO.cleanup()
