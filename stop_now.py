import serial, time
s=serial.Serial('COM7',115200,timeout=0.5)
s.write(b'\x02'); time.sleep(0.5)
s.write(b'\x03'); time.sleep(0.5)
s.write(b'\x03'); time.sleep(0.6)
print(s.read(8192))
s.close()
