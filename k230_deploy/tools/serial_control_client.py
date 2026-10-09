"""Control K230 UART1 through a USB-to-TTL adapter."""

import argparse
import time

import serial


DEFAULT_BAUDRATE = 152000


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
                    if text in ("START", "STOP"):
                        break
        return lines


def main():
    parser = argparse.ArgumentParser(description="Control the K230 main program")
    parser.add_argument(
        "command",
        choices=("start", "stop"),
    )
    parser.add_argument("--port", required=True, help="USB-to-TTL adapter port, for example COM8")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE)
    args = parser.parse_args()
    port = args.port
    print("K230 port:", port)
    payload = {
        "start": b"\x01",
        "stop": b"\x00",
    }[args.command]
    for line in send_command(port, payload, args.baudrate):
        print(line)


if __name__ == "__main__":
    main()
