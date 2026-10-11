from __future__ import annotations

import sys

import uvicorn

from .config import Config, build_config
from .main import create_app
from .net import find_available_port


def resolve_port(config: Config) -> int:
    if not config.port_search:
        return config.port
    try:
        return find_available_port(config.host, config.port)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error


def display_host(host: str) -> str:
    return "localhost" if host in {"", "0.0.0.0"} else host


def run() -> None:
    config = build_config()
    port = resolve_port(config)
    if port != config.port:
        print(f"Port {config.port} is busy; using {port} instead.", flush=True)
    print(f"Verde de Novo running on http://{display_host(config.host)}:{port}", flush=True)
    if config.reload:
        uvicorn.run("server.main:app", host=config.host, port=port, reload=True)
        return
    uvicorn.run(create_app(config), host=config.host, port=port)


if __name__ == "__main__":
    run()
