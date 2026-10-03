import serial, time
s=serial.Serial('COM7',115200,timeout=1)
s.write(b'\x03\x03')
time.sleep(0.5)
s.write(b'\x03')
time.sleep(1.0)
data=s.read_all()
print(data.decode('utf-8','replace'))
s.close()
