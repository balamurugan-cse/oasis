from __future__ import annotations

import argparse
import socket
import threading


def receive_messages(sock: socket.socket) -> None:
    reader = sock.makefile("r", encoding="utf-8", newline="\n")
    try:
        for line in reader:
            print(line.rstrip("\r\n"))
    finally:
        reader.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Connect to the chat server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host to connect to")
    parser.add_argument("--port", type=int, default=5555, help="Server port to connect to")
    parser.add_argument("--name", help="Display name for the chat")
    args = parser.parse_args()

    name = args.name or input("Enter your name: ").strip() or "Anonymous"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))
    sock.sendall((name + "\n").encode("utf-8"))

    receiver = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receiver.start()

    try:
        while True:
            message = input()
            if not message:
                continue
            sock.sendall((message + "\n").encode("utf-8"))
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()