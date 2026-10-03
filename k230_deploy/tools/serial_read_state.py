import serial, time
s=serial.Serial('COM7',115200,timeout=0.2)
try:
    end=time.time()+6
    buf=b''
    while time.time()<end:
        b=s.read(4096)
        if b: buf+=b
    text=buf.decode('utf-8','replace')
    print('STATS_SEEN=', 'STATS FPS=' in text)
    for line in text.splitlines():
        if 'AUTOSTART' in line or 'rear vehicle ready' in line or 'STATS FPS=' in line:
            print(line)
finally:
    s.close()
