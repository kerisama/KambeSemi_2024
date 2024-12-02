import subprocess
import os
import time

#os.system("mpg321 sample1.mp3")
subprocess.Popen(['aplay', 'test.wav'])
"""
print("unmute")
os.system("amixer sset Master on")
subprocess.Popen(['mpg321', 'sample1.mp3'])
time.sleep(8)
"""
"""
print("mute")
os.system("amixer sset Master off")
subprocess.Popen(['mpg321', 'sample1.mp3'])
time.sleep(8)

print("unmute")
os.system("amixer sset Master on")
subprocess.Popen(['mpg321', 'sample1.mp3'])
"""

