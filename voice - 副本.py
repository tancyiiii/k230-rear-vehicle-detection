# -*- coding: utf-8 -*-

"""K230 板载无源蜂鸣器示例。

蜂鸣器必须通过官方的 YbBuzzer 封装控制，不要直接使用
machine.PWM(Pin(42))。YbBuzzer 内部已经配置了正确的 PWM 通道。
"""

import os
import time

from ybUtils.YbBuzzer import YbBuzzer


# 每轮旋律结束后的间隔（秒）
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


# 音符频率（Hz）
C5 = 523
D5 = 587
E5 = 659
F5 = 698
G5 = 784
A5 = 880
B5 = 988
C6 = 1047
D6 = 1175
BEAT = 0.3


def play_national_anthem(buzzer):
    """播放《义勇军进行曲》的简化近似主旋律。"""
    notes = [
        # 起来！不愿做奴隶的人们！
        (E5, BEAT), (E5, BEAT), (G5, BEAT), (A5, BEAT),
        (C6, BEAT), (C6, BEAT), (A5, BEAT), (G5, BEAT * 2),
        (E5, BEAT), (E5, BEAT), (G5, BEAT), (A5, BEAT),
        (C6, BEAT), (C6, BEAT), (A5, BEAT), (G5, BEAT * 2),

        # 把我们的血肉筑成我们新的长城！
        (G5, BEAT), (G5, BEAT), (A5, BEAT), (C6, BEAT),
        (D6, BEAT), (D6, BEAT), (C6, BEAT), (A5, BEAT),
        (G5, BEAT), (G5, BEAT), (E5, BEAT), (G5, BEAT),
        (A5, BEAT), (C6, BEAT), (A5, BEAT), (G5, BEAT * 2),

        # 中华民族到了最危险的时候！
        (E5, BEAT), (G5, BEAT), (D5, BEAT), (D5, BEAT),
        (E5, BEAT), (G5, BEAT), (C6, BEAT * 2),

        # 每个人被迫着发出最后的吼声！
        (C6, BEAT), (A5, BEAT), (G5, BEAT), (E5, BEAT),
        (G5, BEAT), (A5, BEAT), (C6, BEAT * 2),
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
        while True:
            # 只播放《义勇军进行曲》，不播放前面的单独示例音。
            play_national_anthem(buzzer)
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
