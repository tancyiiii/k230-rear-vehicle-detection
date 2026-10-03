import serial, sys, time
s=serial.Serial('COM7',115200,timeout=0.2)
try:
    end=time.time()+60
    buf=b''
    while time.time()<end:
        b=s.read(4096)
        if b:
            buf+=b
            text=b.decode('utf-8','replace')
            sys.stdout.write(text)
            sys.stdout.flush()
finally:
    s.close()
