import serial
import sys
import time

ser = serial.Serial("COM7", 115200, timeout=0.2)
buf = bytearray()
try:
    time.sleep(1)
    # Stop any running main.py and wait for the normal REPL prompt.
    deadline = time.time() + 12
    while time.time() < deadline:
        ser.write(b"\x03")
        time.sleep(0.35)
        chunk = ser.read(4096)
        if chunk:
            buf.extend(chunk)
            sys.stdout.write(chunk.decode("utf-8", "replace"))
            sys.stdout.flush()
        if b">>>" in bytes(buf[-4096:]):
            break
    # Soft reboot from the REPL prompt.
    ser.write(b"\x04")
    start = time.time()
    while time.time() - start < 25:
        chunk = ser.read(4096)
        if chunk:
            buf.extend(chunk)
            sys.stdout.write(chunk.decode("utf-8", "replace"))
            sys.stdout.flush()
    text = buf.decode("utf-8", "replace")
    print("\n=== BOOT_MONITOR_2_DONE ===")
    print("SOFT_REBOOT_SEEN=", "soft reboot" in text.lower())
    print("AUTOSTART_SEEN=", "AUTOSTART" in text)
    print("MODEL_READY_SEEN=", "rear vehicle ready" in text)
    print("STATS_SEEN=", "STATS FPS=" in text)
finally:
    ser.close()
