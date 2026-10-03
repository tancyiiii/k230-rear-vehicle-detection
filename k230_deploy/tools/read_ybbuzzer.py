import serial, sys, time
s=serial.Serial('COM7',115200,timeout=0.2)
buf=bytearray()
try:
    time.sleep(2)
    for _ in range(8):
        s.write(b'\x03')
        time.sleep(0.25)
        chunk=s.read(4096)
        if chunk:
            buf.extend(chunk)
            if b'>>>' in bytes(buf[-4096:]):
                break
    s.write(b'\x01')
    time.sleep(0.4)
    code = (
        b"p='/sdcard/ybUtils/YbBuzzer.py'\r\n"
        b"print('FILE_START')\r\n"
        b"print(open(p).read())\r\n"
        b"print('FILE_END')\r\n"
    )
    s.write(code)
    time.sleep(0.3)
    s.write(b'\x04')
    time.sleep(2.0)
    data=s.read_all()
    sys.stdout.write(data.decode('utf-8','replace'))
finally:
    s.close()
