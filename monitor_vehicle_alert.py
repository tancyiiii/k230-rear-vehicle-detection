import serial, time
s=serial.Serial('COM7',115200,timeout=0.5)
s.write(b'\x04')
time.sleep(0.8)
buf=bytearray(s.read(8192))
end=time.time()+20
while time.time()<end:
    data=s.read(4096)
    if data:
        buf.extend(data)
text=bytes(buf).decode('utf-8','replace')
print(text)
print('CHECK', 'vehicle_speaker: True' in text, 'speaker ready: rate=44100' in text, 'error' not in text.lower(), 'STATS' in text)
s.close()
