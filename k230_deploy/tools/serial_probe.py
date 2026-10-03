import serial, sys, time
s=serial.Serial('COM7',115200,timeout=0.2)
try:
    time.sleep(4)
    print('--- initial ---')
    print(s.read_all().decode('utf-8','replace'))
    for i in range(8):
        s.write(b'\x03')
        time.sleep(0.4)
    print('--- after ctrl-c ---')
    print(s.read_all().decode('utf-8','replace'))
    s.write(b'\r\n')
    time.sleep(0.5)
    print('--- after enter ---')
    print(s.read_all().decode('utf-8','replace'))
finally:
    s.close()
