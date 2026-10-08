"""Host-side client for controlling the K230 over its USB CDC serial port."""

import argparse
import time

import serial
from serial.tools import list_ports


K230_VID = 0x1209
K230_PID = 0xABD1
DEFAULT_BAUDRATE = 2000000


def find_k230_port():
    matches = []
    for port in list_ports.comports():
        if port.vid == K230_VID and port.pid == K230_PID:
            matches.append(port.device)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise RuntimeError("K230 communication port not found; connect the board and use --port COMx")
    raise RuntimeError("multiple K230 ports found: {}; use --port COMx".format(", ".join(matches)))


def send_command(port, command, baudrate=DEFAULT_BAUDRATE, timeout=2.0):
    payload = command if isinstance(command, bytes) else (command.strip() + "\n").encode("ascii")
    with serial.Serial(
        port,
        baudrate=baudrate,
        timeout=timeout,
        write_timeout=timeout,
        dsrdtr=False,
        rtscts=False,
    ) as connection:
        connection.reset_input_buffer()
        connection.write(payload)
        connection.flush()
        deadline = time.time() + timeout
        lines = []
        while time.time() < deadline:
            line = connection.readline()
            if line:
                text = line.decode("utf-8", "replace").strip()
                if text:
                    lines.append(text)
                    if text.startswith("CTRL "):
                        break
        return lines


def main():
    parser = argparse.ArgumentParser(description="Control the K230 main program")
    parser.add_argument(
        "command",
        choices=("start", "stop", "status", "ping", "start-text", "stop-text"),
    )
    parser.add_argument("--port", help="port shown on the computer directly connected to the K230")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE)
    args = parser.parse_args()
    port = args.port or find_k230_port()
    print("K230 port:", port)
    payload = {
        "start": b"\x01",
        "stop": b"\x00",
        "start-text": "START",
        "stop-text": "STOP",
    }.get(args.command, args.command.upper())
    for line in send_command(port, payload, args.baudrate):
        print(line)


if __name__ == "__main__":
    main()
