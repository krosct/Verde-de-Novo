from __future__ import annotations

import socket

import pytest

from server.net import find_available_port, is_port_free


def bind_listening_socket() -> tuple[socket.socket, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    return sock, sock.getsockname()[1]


def test_is_port_free_true_for_released_port() -> None:
    sock, port = bind_listening_socket()
    sock.close()
    assert is_port_free("127.0.0.1", port) is True


def test_is_port_free_false_while_listening() -> None:
    sock, port = bind_listening_socket()
    try:
        assert is_port_free("127.0.0.1", port) is False
    finally:
        sock.close()


def test_find_available_port_skips_busy_port() -> None:
    sock, port = bind_listening_socket()
    try:
        chosen = find_available_port("127.0.0.1", port, max_attempts=10)
        assert chosen > port
        assert is_port_free("127.0.0.1", chosen) is True
    finally:
        sock.close()


def test_find_available_port_raises_when_none_free() -> None:
    sock, port = bind_listening_socket()
    try:
        with pytest.raises(RuntimeError):
            find_available_port("127.0.0.1", port, max_attempts=1)
    finally:
        sock.close()
