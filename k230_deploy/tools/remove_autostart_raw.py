import serial, sys, time
p=serial.Serial('COM7',115200,timeout=0.2)
buf=bytearray()
try:
    time.sleep(6)
    try: buf.extend(p.read_all())
    except Exception: pass
    for _ in range(20):
        p.write(b'\x03')
        time.sleep(0.35)
        try:
            d=p.read(4096)
            if d:
                buf.extend(d)
                sys.stdout.write(d.decode('utf-8','replace'))
                sys.stdout.flush()
        except Exception:
            pass
        if b'>>>' in bytes(buf[-4096:]):
            break
    p.write(b'\x01')
    time.sleep(0.4)
    cmd=(
        b"import os\r\n"
        b"try:\r\n"
        b" os.remove('/sdcard/main.py')\r\n"
        b"except OSError:\r\n"
        b" pass\r\n"
        b"print('REMOVED_MAIN')\r\n"
    )
    p.write(cmd)
    time.sleep(0.3)
    p.write(b'\x04')
    time.sleep(2)
    sys.stdout.write(p.read_all().decode('utf-8','replace'))
finally:
    p.close()
