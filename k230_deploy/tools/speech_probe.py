# -*- coding: utf-8 -*-
import time

from media.media import MediaManager
from media.pyaudio import PyAudio, paInt16
from ybUtils.YbSpeaker import YbSpeaker


PCM_PATH = "/sdcard/rear_vehicle/attention_person.pcm"
RATE = 44100
CHUNK = 1024


audio = PyAudio()
audio.initialize(CHUNK)
MediaManager.init()
speaker = YbSpeaker()
speaker.enable()
stream = None
try:
    with open(PCM_PATH, "rb") as pcm_file:
        speech = pcm_file.read()
    if not speech or len(speech) % 4 != 0:
        raise ValueError("invalid stereo PCM data")

    stream = audio.open(
        format=paInt16,
        channels=2,
        rate=RATE,
        input=0,
        output=1,
        frames_per_buffer=CHUNK,
    )
    frame_bytes = CHUNK * 4
    for offset in range(0, len(speech), frame_bytes):
        chunk = speech[offset:offset + frame_bytes]
        if len(chunk) < frame_bytes:
            chunk += bytes(frame_bytes - len(chunk))
        stream.write(chunk)
    time.sleep_ms(300)
    print("VOICE_OK", len(speech))
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
        audio.terminate()
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
