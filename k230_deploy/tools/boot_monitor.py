import serial
import sys
import time

port = "COM7"
ser = serial.Serial(port, 115200, timeout=0.2)
try:
    try:
        ser.dtr = True
        ser.rts = True
    except Exception:
        pass
    time.sleep(0.5)
    ser.write(b"\x03\x03")
    time.sleep(0.5)
    try:
        ser.read_all()
    except Exception:
        pass
    ser.write(b"\x04")
    start = time.time()
    buf = bytearray()
    while time.time() - start < 25.0:
        chunk = ser.read(4096)
        if chunk:
            buf.extend(chunk)
            sys.stdout.write(chunk.decode("utf-8", "replace"))
            sys.stdout.flush()
    print("\n=== BOOT_MONITOR_DONE ===")
    text = buf.decode("utf-8", "replace")
    print("AUTOSTART_SEEN=", "AUTOSTART" in text)
    print("MODEL_READY_SEEN=", "rear vehicle ready" in text)
    print("STATS_SEEN=", "STATS FPS=" in text)
finally:
    ser.close()
