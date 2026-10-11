from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import Config, build_config
from .pipeline import InvalidImage, analyze, empty_response
from .vendor import get_vendor

VENDOR_OUTAGE_MESSAGE = "Não foi possível analisar agora. Tente de novo em instantes."
INVALID_IMAGE_MESSAGE = "Não reconheci um arquivo de imagem válido."

_METADATA_MARKERS = {0xE1, 0xE2, 0xED, 0xFE}


def is_jpeg(data: bytes) -> bool:
    return data[:2] == b"\xff\xd8"


def strip_jpeg_metadata(data: bytes) -> bytes:
    if not is_jpeg(data):
        return data
    output = bytearray(data[:2])
    index = 2
    total = len(data)
    while index + 4 <= total:
        if data[index] != 0xFF:
            output.extend(data[index:])
            break
        marker = data[index + 1]
        if marker == 0xDA:
            output.extend(data[index:])
            break
        if marker == 0xD8 or marker == 0x01 or 0xD0 <= marker <= 0xD7:
            output.extend(data[index : index + 2])
            index += 2
            continue
        segment_length = int.from_bytes(data[index + 2 : index + 4], "big")
        if segment_length < 2 or index + 2 + segment_length > total:
            output.extend(data[index:])
            break
        if marker not in _METADATA_MARKERS:
            output.extend(data[index : index + 2 + segment_length])
        index += 2 + segment_length
    return bytes(output)


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = max(1, limit)
        self._window = max(1, window_seconds)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                return False
            hits.append(now)
            return True


def create_app(config: Config | None = None) -> FastAPI:
    cfg = config if config is not None else build_config([])
    app = FastAPI(title="Verde de Novo API", docs_url=None, redoc_url=None, openapi_url=None)
    limiter = RateLimiter(cfg.rate_limit, cfg.rate_window_seconds)
    vendor = get_vendor(cfg)

    @app.get("/api/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/plant", response_model=None)
    def plant(request: Request, image: Annotated[UploadFile, File()]) -> dict[str, object] | JSONResponse:
        client_key = request.client.host if request.client else "unknown"
        if not limiter.allow(client_key):
            raise HTTPException(status_code=429, detail="Muitas tentativas em pouco tempo. Espere um instante.")

        raw = image.file.read()
        if len(raw) == 0 or not is_jpeg(raw):
            raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE)
        if len(raw) > cfg.max_image_bytes:
            raise HTTPException(status_code=413, detail="A foto é grande demais. Tente uma menor.")

        cleaned = strip_jpeg_metadata(raw)
        try:
            return analyze(cleaned, vendor, cfg.confidence_threshold)
        except InvalidImage as error:
            raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE) from error
        except Exception:  # noqa: BLE001 - any vendor failure must degrade to a friendly message
            return JSONResponse(content=empty_response("unavailable", VENDOR_OUTAGE_MESSAGE, ok=False))

    _mount_static(app, cfg.static_dir)
    return app


def _mount_static(app: FastAPI, static_dir: Path) -> None:
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


app = create_app()
