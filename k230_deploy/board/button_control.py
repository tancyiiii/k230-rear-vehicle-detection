# -*- coding: utf-8 -*-
"""Debounced single-button run/stop control for the 320 deployment."""

import time

try:
    from machine import Pin
except BaseException:
    Pin = None


# Connect a momentary button between GPIO21 and GND.
CONTROL_GPIO = 21
BUTTON_ACTIVE_LEVEL = 0
BUTTON_DEBOUNCE_MS = 60
BUTTON_POLL_MS = 20
START_ENABLED = True

_pin = None
_enabled = START_ENABLED
_raw_level = None
_stable_level = None
_changed_ms = 0
_last_poll_ms = 0


def initialize():
    """Initialize the input and preserve the current run state."""
    global _pin, _raw_level, _stable_level, _changed_ms, _last_poll_ms
    if Pin is None:
        print("button control unavailable: machine.Pin")
        return
    try:
        _pin = Pin(CONTROL_GPIO, Pin.IN, Pin.PULL_UP)
        level = _pin.value()
        _raw_level = level
        _stable_level = level
        now_ms = time.ticks_ms()
        _changed_ms = now_ms
        _last_poll_ms = now_ms
        print("button control ready: GPIO{} active={} enabled={}".format(
            CONTROL_GPIO, BUTTON_ACTIVE_LEVEL, _enabled
        ))
    except BaseException as error:
        _pin = None
        print("button control init failed:", error)


def poll():
    """Debounce the button and return whether recognition should run."""
    global _raw_level, _stable_level, _changed_ms, _last_poll_ms, _enabled
    if _pin is None:
        return _enabled

    now_ms = time.ticks_ms()
    if (
        _last_poll_ms != 0
        and time.ticks_diff(now_ms, _last_poll_ms) < BUTTON_POLL_MS
    ):
        return _enabled
    _last_poll_ms = now_ms

    level = _pin.value()
    if level != _raw_level:
        _raw_level = level
        _changed_ms = now_ms
        return _enabled
    if (
        level != _stable_level
        and time.ticks_diff(now_ms, _changed_ms) >= BUTTON_DEBOUNCE_MS
    ):
        _stable_level = level
        if level == BUTTON_ACTIVE_LEVEL:
            _enabled = not _enabled
            print("button control: {}".format(
                "START" if _enabled else "STOP"
            ))
    return _enabled


def is_enabled():
    return _enabled
