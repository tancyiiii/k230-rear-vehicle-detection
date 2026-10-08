# -*- coding: utf-8 -*-
import math
import time
from array import array
from media.media import MediaManager
from media.pyaudio import PyAudio, paInt16
from ybUtils.YbSpeaker import YbSpeaker

RATE = 44100
CHUNK = 1024
AMPLITUDE = int(32767 * 0.08)

p = PyAudio()
p.initialize(CHUNK)
MediaManager.init()
speaker = YbSpeaker()
speaker.enable()
stream = None
try:
    stream = p.open(
        format=paInt16,
        channels=2,
        rate=RATE,
        input=0,
        output=1,
        frames_per_buffer=CHUNK,
    )
    samples = array("h")
    for i in range(int(RATE * 0.35)):
        value = int(AMPLITUDE * math.sin(2.0 * math.pi * 1200 * i / RATE))
        samples.append(value)
        samples.append(value)
    data = bytes(samples)
    frame_bytes = CHUNK * 4
    for offset in range(0, len(data), frame_bytes):
        chunk = data[offset:offset + frame_bytes]
        if len(chunk) < frame_bytes:
            chunk += bytes(frame_bytes - len(chunk))
        result = stream.write(chunk)
        print("write", result)
    time.sleep_ms(300)
    print("TONE_OK")
finally:
    if stream is not None:
        try:
            stream.stop_stream()
        except BaseException:
            pass
        try:
            stream.close()
        except BaseException:
            pass
    try:
        p.terminate()
    except BaseException:
        pass
    try:
        speaker.disable()
    except BaseException:
        pass
    try:
        MediaManager.deinit()
    except BaseException:
        pass
