# -*- coding: utf-8 -*-

"""K230 板载无源蜂鸣器示例。

蜂鸣器必须通过官方的 YbBuzzer 封装控制，不要直接使用
machine.PWM(Pin(42))。YbBuzzer 内部已经配置了正确的 PWM 通道。
"""

import os
import time

from ybUtils.YbBuzzer import YbBuzzer


# 每轮蜂鸣结束后的间隔（秒）
LOOP_DELAY_SECONDS = 0.5


def exitpoint():
    """让 K230 IDE 的停止按钮能够中断等待。"""
    try:
        os.exitpoint()
    except AttributeError:
        pass


def sleep_seconds(seconds):
    """分段等待，避免长时间等待时无法响应停止请求。"""
    end_time = time.ticks_ms() + int(seconds * 1000)
    while time.ticks_diff(end_time, time.ticks_ms()) > 0:
        exitpoint()
        remaining = time.ticks_diff(end_time, time.ticks_ms())
        time.sleep_ms(min(remaining, 100))


def play_two_beeps(buzzer):
    """播放两声短蜂鸣。"""
    for beep_index in range(2):
        exitpoint()
        buzzer.on(2700, 50, 0.08)
        sleep_seconds(0.08)
        if beep_index == 0:
            sleep_seconds(0.07)
    buzzer.off()


def main():
    buzzer = YbBuzzer()
    try:
        while True:
            play_two_beeps(buzzer)
            buzzer.off()
            sleep_seconds(LOOP_DELAY_SECONDS)
    finally:
        # 官方接口提供 off()，脚本结束前必须确保蜂鸣器静音。
        try:
            buzzer.off()
        except BaseException:
            pass


try:
    main()
except KeyboardInterrupt:
    pass
except BaseException as error:
    print("蜂鸣器异常:", error)
finally:
    try:
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
    except BaseException:
        pass
