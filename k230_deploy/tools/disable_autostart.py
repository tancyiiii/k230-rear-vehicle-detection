import serial
import sys
import time

port = "COM7"
ser = serial.Serial(port, 115200, timeout=0.2)
try:
    time.sleep(5.0)
    try:
        ser.read_all()
    except Exception:
        pass
    for _ in range(5):
        ser.write(b"\x03")
        time.sleep(0.3)
    try:
        ser.read_all()
    except Exception:
        pass
    ser.write(b"import os\r\n")
    time.sleep(0.5)
    ser.write(b"try:\r\n")
    time.sleep(0.2)
    ser.write(b" os.remove('/sdcard/main.py')\r\n")
    time.sleep(0.2)
    ser.write(b"except OSError:\r\n")
    time.sleep(0.2)
    ser.write(b" pass\r\n")
    time.sleep(0.3)
    ser.write(b"\r\n")
    time.sleep(1.0)
    ser.write(b"print('MAIN_REMOVED', 'main.py' in os.listdir('/sdcard'))\r\n")
    time.sleep(1.0)
    data = ser.read_all()
    sys.stdout.write(data.decode("utf-8", "replace"))
finally:
    ser.close()
