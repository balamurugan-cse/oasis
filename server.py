from __future__ import annotations

import argparse
import socket
import threading
from contextlib import suppress


clients: set[socket.socket] = set()
clients_lock = threading.Lock()


def broadcast(message: str, sender: socket.socket | None = None) -> None:
    data = (message + "\n").encode("utf-8")
    with clients_lock:
        recipients = list(clients)

    for client in recipients:
        if client is sender:
            continue
        with suppress(OSError):
            client.sendall(data)


def remove_client(client: socket.socket) -> None:
    with clients_lock:
        clients.discard(client)
    with suppress(OSError):
        client.close()


def handle_client(client: socket.socket, address: tuple[str, int]) -> None:
    name = f"{address[0]}:{address[1]}"
    reader = client.makefile("r", encoding="utf-8", newline="\n")

    try:
        try:
            first_line = reader.readline()
        except OSError:
            return

        if first_line:
            candidate = first_line.strip()
            if candidate:
                name = candidate

        broadcast(f"* {name} joined the chat")

        for line in reader:
            message = line.rstrip("\r\n")
            if not message:
                continue
            broadcast(f"{name}: {message}", sender=client)
    finally:
        broadcast(f"* {name} left the chat")
        with suppress(Exception):
            reader.close()
        remove_client(client)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the chat server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=5555, help="Port to listen on")
    args = parser.parse_args()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((args.host, args.port))
    server_socket.listen()

    print(f"Chat server listening on {args.host}:{args.port}")

    try:
        while True:
            client, address = server_socket.accept()
            client.setblocking(True)
            with clients_lock:
                clients.add(client)
            thread = threading.Thread(target=handle_client, args=(client, address), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        with clients_lock:
            active_clients = list(clients)
            clients.clear()
        for client in active_clients:
            with suppress(OSError):
                client.close()
        server_socket.close()


if __name__ == "__main__":
    main()