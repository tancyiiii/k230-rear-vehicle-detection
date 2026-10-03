import serial, sys, time

ser = serial.Serial("COM7", 115200, timeout=0.2)
buf = bytearray()
try:
    time.sleep(2)
    for _ in range(8):
        ser.write(b"\x03")
        time.sleep(0.25)
        data = ser.read(4096)
        if data:
            buf.extend(data)
            sys.stdout.write(data.decode("utf-8", "replace"))
            sys.stdout.flush()
        if b">>>" in bytes(buf[-2048:]):
            break
    ser.write(b"\x01")
    time.sleep(0.3)
    cleanup = (
        b"import os\r\n"
        b"try:\r\n"
        b" os.remove('/sdcard/rear_vehicle/boot_error.txt')\r\n"
        b"except OSError:\r\n"
        b" pass\r\n"
        b"print('BOOT_ERROR_CLEANED')\r\n"
    )
    ser.write(cleanup)
    time.sleep(0.3)
    ser.write(b"\x04")
    time.sleep(1.0)
    data = ser.read_all()
    if data:
        buf.extend(data)
        sys.stdout.write(data.decode("utf-8", "replace"))
        sys.stdout.flush()
    ser.write(b"\x04")
    start = time.time()
    while time.time() - start < 12:
        data = ser.read(4096)
        if data:
            buf.extend(data)
            sys.stdout.write(data.decode("utf-8", "replace"))
            sys.stdout.flush()
    text = buf.decode("utf-8", "replace")
    print("\n=== FINAL_BOOT_CHECK ===")
    print("AUTOSTART_SEEN=", "AUTOSTART" in text)
    print("MODEL_READY_SEEN=", "rear vehicle ready" in text)
    print("STATS_SEEN=", "STATS FPS=" in text)
finally:
    ser.close()
