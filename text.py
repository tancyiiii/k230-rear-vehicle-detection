# -*- coding: utf-8 -*-

"""K230 板载无源蜂鸣器示例。

蜂鸣器必须通过官方的 YbBuzzer 封装控制，不要直接使用
machine.PWM(Pin(42))。YbBuzzer 内部已经配置了正确的 PWM 通道。
"""

import os
import time

from ybUtils.YbBuzzer import YbBuzzer


# 是否在基础示例后播放《一闪一闪亮晶晶》
PLAY_MELODY = True


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


# 音符频率（Hz）
C5 = 523
D5 = 587
E5 = 659
F5 = 698
G5 = 784
A5 = 880
B5 = 988
BEAT = 0.3


def play_twinkle(buzzer):
    """播放《一闪一闪亮晶晶》。"""
    notes = [
        (C5, BEAT), (C5, BEAT), (G5, BEAT), (G5, BEAT),
        (A5, BEAT), (A5, BEAT), (G5, BEAT * 2),
        (F5, BEAT), (F5, BEAT), (E5, BEAT), (E5, BEAT),
        (D5, BEAT), (D5, BEAT), (C5, BEAT * 2),
    ]

    for frequency, duration in notes:
        exitpoint()
        # 参数依次为：频率、音量（百分比）、持续时间（秒）。
        buzzer.on(frequency, 50, duration)
        sleep_seconds(0.1)

    buzzer.off()


def main():
    buzzer = YbBuzzer()
    try:
        # 示例 1：使用默认参数短鸣一声。
        buzzer.beep()
        sleep_seconds(3)

        # 示例 2：2000 Hz、音量 50%、持续 0.5 秒。
        buzzer.on(2000, 50, 0.5)
        sleep_seconds(3)

        # 示例 3：1000 Hz 警报声，连续三次。
        for _ in range(3):
            exitpoint()
            buzzer.on(1000, 50, 0.1)
            sleep_seconds(0.1)

        buzzer.off()
        sleep_seconds(1)

        if PLAY_MELODY:
            play_twinkle(buzzer)
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
