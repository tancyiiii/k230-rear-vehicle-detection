# -*- coding: utf-8 -*-
"""Non-blocking USB-serial control for the K230 application."""

import sys
import time

try:
    import _thread
except BaseException:
    _thread = None


class SerialControl:
    """Accept START, STOP, STATUS and PING commands from the USB CDC port."""

    def __init__(self):
        self.enabled = True
        self._buffer = ""
        self._stream = getattr(sys, "stdin", None)
        self._poller = None
        self._reader_started = False
        try:
            if _thread is not None and self._stream is not None:
                try:
                    _thread.start_new_thread(self._reader, ())
                    self._reader_started = True
                except BaseException:
                    self._reader_started = False
            if self._reader_started:
                print("serial control ready: stdin reader")
            else:
                import uselect
                self._poller = uselect.poll()
                self._poller.register(self._stream, uselect.POLLIN)
                print("serial control ready: poll reader")
        except BaseException as error:
            print("serial control unavailable:", error)

    def _reply(self, message):
        try:
            print("CTRL " + message)
            sys.stdout.flush()
        except BaseException:
            pass

    def _set_state(self, enabled):
        self.enabled = enabled
        self._reply("OK RUNNING" if enabled else "OK STOPPED")

    def _handle(self, command):
        command = command.strip().upper()
        if not command:
            return
        if command in ("START", "RUN", "RUN 1"):
            self._set_state(True)
        elif command in ("STOP", "PAUSE", "RUN 0"):
            self._set_state(False)
        elif command == "STATUS":
            self._reply("STATUS " + ("RUNNING" if self.enabled else "STOPPED"))
        elif command == "PING":
            self._reply("PONG")
        else:
            self._reply("ERROR UNKNOWN_COMMAND")

    def _consume(self, char):
        if char == "\x01" or char == b"\x01":
            self._set_state(True)
            return
        if char == "\x00" or char == b"\x00":
            self._set_state(False)
            return
        if isinstance(char, bytes):
            if char in (b"\r", b"\n"):
                self._handle(self._buffer)
                self._buffer = ""
                return
            try:
                char = char.decode("ascii")
            except BaseException:
                return
        if char in ("\r", "\n"):
            self._handle(self._buffer)
            self._buffer = ""
        else:
            self._buffer += char
            if len(self._buffer) > 64:
                self._buffer = ""
                self._reply("ERROR COMMAND_TOO_LONG")

    def _reader(self):
        """Block in the firmware stdin reader so USB CDC input is not lost."""
        while True:
            try:
                char = self._stream.read(1)
                if char:
                    self._consume(char)
                else:
                    time.sleep_ms(10)
            except BaseException as error:
                print("serial control reader error:", error)
                return

    def poll(self):
        """Read all currently available input without blocking the AI loop."""
        if self._reader_started:
            return self.enabled
        if self._poller is None:
            return self.enabled
        for _ in range(64):
            try:
                if not self._poller.poll(0):
                    break
                char = self._stream.read(1)
            except BaseException:
                break
            if not char:
                break
            self._consume(char)
        return self.enabled
