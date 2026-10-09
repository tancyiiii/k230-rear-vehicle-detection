# -*- coding: utf-8 -*-
"""Non-blocking UART1 run/stop control for the K230 application."""

try:
    from machine import FPIOA, UART
except BaseException:
    FPIOA = None
    UART = None

UART_ID = 1
UART_TX_GPIO = 9
UART_RX_GPIO = 10
UART_BAUDRATE = 152000
CMD_STOP = 0x00
CMD_START = 0x01


class SerialControl:
    def __init__(self):
        self.enabled = True
        self._uart = None
        try:
            if FPIOA is None or UART is None:
                raise RuntimeError("machine UART unavailable")
            fpioa = FPIOA()
            fpioa.set_function(UART_TX_GPIO, FPIOA.UART1_TXD)
            fpioa.set_function(UART_RX_GPIO, FPIOA.UART1_RXD)
            self._uart = UART(UART_ID, baudrate=UART_BAUDRATE, bits=8, parity=0, stop=1)
            print("UART1 control ready: TX=GPIO9 RX=GPIO10 baud=152000")
        except BaseException as error:
            print("UART1 control unavailable:", error)

    def _reply(self, message):
        print(message)
        if self._uart is not None:
            try:
                self._uart.write((message + "\r\n").encode("ascii"))
            except BaseException as error:
                print("UART1 reply error:", error)

    def _consume(self, data):
        for value in data:
            if value == CMD_START:
                self.enabled = True
                self._reply("START")
            elif value == CMD_STOP:
                self.enabled = False
                self._reply("STOP")

    def poll(self):
        if self._uart is None:
            return self.enabled
        try:
            if self._uart.any():
                data = self._uart.read()
                if data:
                    self._consume(data)
        except BaseException as error:
            print("UART1 control read error:", error)
        return self.enabled

    def close(self):
        if self._uart is not None:
            try:
                self._uart.deinit()
            except BaseException:
                pass
            self._uart = None
