# -*- coding: utf-8 -*-
"""Play the Chinese prompt ``试音`` at four speaker volume levels.

Copy this file and the four ``test_sound_*.pcm`` files to the board, then run
it from CanMV IDE.  The PCM files are 44.1 kHz, stereo, signed 16-bit data.
"""

import time

from media.media import MediaManager
from media.pyaudio import PyAudio, paInt16
from ybUtils.YbSpeaker import YbSpeaker


RATE = 44100
CHUNK = 1024
FRAME_BYTES = CHUNK * 4  # stereo, 16-bit samples
GAP_MS = 700

VOLUME_LEVELS = (
    ("1/4 (25%)", "test_sound_25.pcm"),
    ("2/4 (50%)", "test_sound_50.pcm"),
    ("3/4 (75%)", "test_sound_75.pcm"),
    ("4/4 (100%)", "test_sound_100.pcm"),
)


def _exitpoint():
    """Let the CanMV IDE stop button interrupt a long playback."""
    try:
        import os

        os.exitpoint()
    except (AttributeError, OSError):
        pass


def _play_file(stream, path):
    with open(path, "rb") as pcm_file:
        while True:
            _exitpoint()
            chunk = pcm_file.read(FRAME_BYTES)
            if not chunk:
                break
            if len(chunk) < FRAME_BYTES:
                chunk += bytes(FRAME_BYTES - len(chunk))
            stream.write(chunk)


def _resolve_pcm_path(filename):
    """Allow the script and assets to be copied as one folder or as a package."""
    candidates = [
        "/sdcard/rear_vehicle/" + filename,
        "/sdcard/rear_vehicle/audio/" + filename,
        "/sdcard/" + filename,
        "/sdcard/audio/" + filename,
        filename,
    ]
    try:
        script_dir = __file__.rsplit("/", 1)[0]
        if script_dir:
            candidates.append(script_dir + "/" + filename)
            candidates.append(script_dir + "/audio/" + filename)
    except (NameError, AttributeError):
        pass
    for path in candidates:
        try:
            with open(path, "rb") as pcm_file:
                size = 0
                while pcm_file.read(FRAME_BYTES):
                    size += 1
            if size == 0:
                raise ValueError("empty PCM file")
            return path
        except OSError:
            pass
    raise OSError("PCM file not found: " + filename)


def main():
    audio = PyAudio()
    speaker = None
    stream = None
    media_initialized = False
    try:
        resolved_levels = []
        for label, filename in VOLUME_LEVELS:
            path = _resolve_pcm_path(filename)
            resolved_levels.append((label, path))
            print("asset ready", label, path)

        print("audio: initialize")
        audio.initialize(CHUNK)
        print("media: initialize")
        MediaManager.init()
        media_initialized = True
        print("speaker: enable")
        speaker = YbSpeaker()
        speaker.enable()
        print("stream: open")
        stream = audio.open(
            format=paInt16,
            channels=2,
            rate=RATE,
            input=0,
            output=1,
            frames_per_buffer=CHUNK,
        )
        print("speaker volume test: 试音")
        for label, path in resolved_levels:
            print("playing", label, path)
            _play_file(stream, path)
            time.sleep_ms(GAP_MS)
        print("speaker volume test complete")
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
        if speaker is not None:
            try:
                speaker.disable()
            except BaseException:
                pass
        if media_initialized:
            try:
                MediaManager.deinit()
            except BaseException:
                pass


try:
    main()
except KeyboardInterrupt:
    pass
except BaseException as error:
    print("speaker volume test failed:", error)
    try:
        import sys

        sys.print_exception(error)
    except BaseException:
        pass
