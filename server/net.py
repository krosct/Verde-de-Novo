from __future__ import annotations

import socket

DEFAULT_MAX_ATTEMPTS = 20
MAX_PORT = 65535


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def find_available_port(host: str, start_port: int, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> int:
    last_port = min(start_port + max_attempts - 1, MAX_PORT)
    for candidate in range(start_port, last_port + 1):
        if is_port_free(host, candidate):
            return candidate
    raise RuntimeError(
        f"No free port found on {host} between {start_port} and {last_port}."
    )
