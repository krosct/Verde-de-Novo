from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_STATIC_DIR = "dist"
DEFAULT_PROVIDER = "stub"
DEFAULT_CONFIDENCE_THRESHOLD = 0.6
DEFAULT_MAX_IMAGE_MB = 2.5
DEFAULT_RATE_LIMIT = 10
DEFAULT_RATE_WINDOW_SECONDS = 60


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    static_dir: Path
    vision_provider: str
    vision_api_key: str
    vision_api_url: str
    confidence_threshold: float
    max_image_bytes: int
    rate_limit: int
    rate_window_seconds: int
    reload: bool
    port_search: bool


def build_config(argv: list[str] | None = None) -> Config:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    args = _build_parser().parse_args(argv)

    max_image_mb = float(_pick(args.max_image_mb, "MAX_IMAGE_MB", str(DEFAULT_MAX_IMAGE_MB)))
    return Config(
        host=_pick(args.host, "HOST", DEFAULT_HOST),
        port=int(_pick(args.port, "PORT", str(DEFAULT_PORT))),
        static_dir=Path(_pick(args.static_dir, "STATIC_DIR", DEFAULT_STATIC_DIR)),
        vision_provider=_pick(args.vision_provider, "VISION_PROVIDER", DEFAULT_PROVIDER),
        vision_api_key=_pick(args.vision_key, "VISION_API_KEY", ""),
        vision_api_url=_pick(args.vision_url, "VISION_API_URL", ""),
        confidence_threshold=float(
            _pick(args.confidence_threshold, "CONFIDENCE_THRESHOLD", str(DEFAULT_CONFIDENCE_THRESHOLD))
        ),
        max_image_bytes=int(max_image_mb * 1024 * 1024),
        rate_limit=int(_pick(args.rate_limit, "RATE_LIMIT", str(DEFAULT_RATE_LIMIT))),
        rate_window_seconds=int(_pick(args.rate_window, "RATE_WINDOW", str(DEFAULT_RATE_WINDOW_SECONDS))),
        reload=_pick_flag(args.reload, "RELOAD", False),
        port_search=_pick_flag(args.port_search, "PORT_SEARCH", True),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="server", description="Verde de Novo backend proxy")
    parser.add_argument("--host", default=None, help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", default=None, help="Bind port (default: 8000)")
    parser.add_argument("--static-dir", default=None, help="Directory with the built frontend (default: dist)")
    parser.add_argument(
        "--vision-provider",
        default=None,
        choices=["stub"],
        help="Vision vendor adapter (default: stub; real vendors are added in server/vendor.py)",
    )
    parser.add_argument("--vision-key", default=None, help="Vendor API key (kept only on the server)")
    parser.add_argument("--vision-url", default=None, help="Vendor endpoint URL for a real provider")
    parser.add_argument("--confidence-threshold", default=None, help="Minimum confidence for each analysis step")
    parser.add_argument("--max-image-mb", default=None, help="Maximum accepted image size in MB")
    parser.add_argument("--rate-limit", default=None, help="Requests allowed per rate window")
    parser.add_argument("--rate-window", default=None, help="Rate window in seconds")
    parser.add_argument("--reload", action=argparse.BooleanOptionalAction, default=None, help="Auto-reload on change")
    parser.add_argument(
        "--port-search",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="If the port is busy, try the next one (default: true)",
    )
    return parser


def _pick(cli_value: str | None, env_name: str, default: str) -> str:
    if cli_value is not None:
        return cli_value
    env_value = os.environ.get(env_name)
    if env_value is not None and env_value != "":
        return env_value
    return default


def _pick_flag(cli_value: bool | None, env_name: str, default: bool) -> bool:
    if cli_value is not None:
        return cli_value
    env_value = os.environ.get(env_name)
    if env_value is not None and env_value != "":
        return env_value.strip().lower() in {"1", "true", "yes", "on"}
    return default
