from __future__ import annotations

import base64
from pathlib import Path

from fastapi.testclient import TestClient

from server.catalog import CONDITIONS, OBSERVATIONS
from server.config import Config
from server.main import create_app, strip_jpeg_metadata
from server.vendor import Box, Finding, GateResult, PartRegion, SpeciesGuess

TINY_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsO"
    "CwkJDRENDg8QEBEQCgwSExIQEw8QEBD/wAALCAACAAIBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAA"
    "AAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AVN//2Q=="
)

FROZEN_KEYS = {
    "ok",
    "status",
    "message",
    "species",
    "alternatives",
    "parts",
    "conditions",
    "care",
    "is_diagnosis",
    "retry",
}


PLANT_OK = GateResult(True, 0.9, "ok")
SUCCULENT = (SpeciesGuess("succulent", "Suculenta", "Crassulaceae", 0.9),)


class ScriptedVendor:
    def __init__(
        self,
        gate: GateResult = PLANT_OK,
        species: tuple[SpeciesGuess, ...] = SUCCULENT,
        parts: tuple[str, ...] = ("leaf", "soil"),
        findings: dict[str, list[Finding]] | None = None,
    ) -> None:
        self.gate = gate
        self.species = list(species)
        self.parts = parts
        self.findings = findings or {}

    def check_plant(self, image: bytes) -> GateResult:
        return self.gate

    def identify_species(self, image: bytes) -> list[SpeciesGuess]:
        return self.species

    def locate_parts(self, image: bytes) -> list[PartRegion]:
        return [PartRegion(part, Box(0.0, 0.0, 1.0, 1.0), 0.9) for part in self.parts]

    def analyze_part(self, crop: bytes, part: str, species_id: str | None) -> list[Finding]:
        return self.findings.get(part, [])


def make_config(**overrides: object) -> Config:
    values: dict[str, object] = {
        "host": "127.0.0.1",
        "port": 8000,
        "static_dir": Path("does-not-exist"),
        "vision_provider": "stub",
        "vision_api_key": "",
        "vision_api_url": "",
        "confidence_threshold": 0.6,
        "max_image_bytes": 2_000_000,
        "rate_limit": 100,
        "rate_window_seconds": 60,
        "reload": False,
        "port_search": True,
    }
    values.update(overrides)
    return Config(**values)  # type: ignore[arg-type]


def client_for(config: Config | None = None) -> TestClient:
    return TestClient(create_app(config or make_config()))


def post_plant(client: TestClient, data: bytes = TINY_JPEG):
    return client.post("/api/plant", files={"image": ("plant.jpg", data, "image/jpeg")})


def client_with(monkeypatch, vendor: ScriptedVendor, **overrides: object) -> TestClient:
    monkeypatch.setattr("server.main.get_vendor", lambda config: vendor)
    return client_for(make_config(**overrides))


def test_health() -> None:
    assert client_for().get("/api/health").json() == {"ok": True}


def test_stub_matches_frozen_schema() -> None:
    response = post_plant(client_for())
    assert response.status_code == 200
    body = response.json()
    assert set(body) == FROZEN_KEYS
    assert body["is_diagnosis"] is False
    assert body["status"] == "analyzed"
    assert body["care"]
    for part in body["parts"]:
        for observation in part["observations"]:
            assert observation["code"] in OBSERVATIONS
    for condition in body["conditions"]:
        assert condition["code"] in CONDITIONS
        assert 0.0 <= condition["confidence"] <= 1.0


def test_not_a_plant_stops_early(monkeypatch) -> None:
    body = post_plant(client_with(monkeypatch, ScriptedVendor(gate=GateResult(False, 0.95, "ok")))).json()
    assert body["status"] == "not_plant"
    assert body["retry"] is True
    assert body["conditions"] == []


def test_dark_photo_asks_for_another(monkeypatch) -> None:
    body = post_plant(client_with(monkeypatch, ScriptedVendor(gate=GateResult(True, 0.9, "dark")))).json()
    assert body["status"] == "bad_image"
    assert "escura" in body["message"]


def test_wet_soil_and_yellow_leaves_point_to_overwatering(monkeypatch) -> None:
    vendor = ScriptedVendor(
        findings={
            "leaf": [Finding("leaf_yellow_lower", 0.85)],
            "soil": [Finding("soil_wet", 0.9)],
        }
    )
    body = post_plant(client_with(monkeypatch, vendor)).json()
    codes = [condition["code"] for condition in body["conditions"]]
    assert codes[0] == "overwatering"
    assert body["species"]["id"] == "succulent"
    assert any(item["topic"] == "growth" for item in body["care"])


def test_low_confidence_species_falls_back_to_generic_care(monkeypatch) -> None:
    vendor = ScriptedVendor(species=(SpeciesGuess("succulent", "Suculenta", "Crassulaceae", 0.3),))
    body = post_plant(client_with(monkeypatch, vendor)).json()
    assert body["species"] is None
    assert body["alternatives"][0]["common_name"] == "Suculenta"
    assert "espécie" in body["message"]
    assert all(item["topic"] != "growth" for item in body["care"])


def test_invented_codes_are_dropped(monkeypatch) -> None:
    vendor = ScriptedVendor(findings={"leaf": [Finding("mosaic_virus", 0.99), Finding("soil_wet", 0.99)]})
    body = post_plant(client_with(monkeypatch, vendor)).json()
    leaf = next(part for part in body["parts"] if part["part"] == "leaf")
    assert leaf["observations"] == []
    assert body["conditions"] == []


def test_vendor_outage_is_friendly(monkeypatch) -> None:
    class BrokenVendor(ScriptedVendor):
        def identify_species(self, image: bytes) -> list[SpeciesGuess]:
            raise RuntimeError("vendor down")

    response = post_plant(client_with(monkeypatch, BrokenVendor()))
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["status"] == "unavailable"
    assert body["retry"] is True


def test_rejects_non_jpeg() -> None:
    assert post_plant(client_for(), data=b"definitely not an image").status_code == 400


def test_rejects_corrupt_jpeg() -> None:
    assert post_plant(client_for(), data=b"\xff\xd8garbage").status_code == 400


def test_rejects_oversized_image() -> None:
    response = post_plant(client_for(make_config(max_image_bytes=4)), data=TINY_JPEG + b"\x00" * 10)
    assert response.status_code == 413


def test_rate_limit_blocks_bursts() -> None:
    client = client_for(make_config(rate_limit=2, rate_window_seconds=60))
    assert post_plant(client).status_code == 200
    assert post_plant(client).status_code == 200
    assert post_plant(client).status_code == 429


def test_strip_jpeg_metadata_removes_exif() -> None:
    app1 = b"\xff\xe1\x00\x10" + b"Exif\x00\x00" + b"\x00" * 8
    cleaned = strip_jpeg_metadata(TINY_JPEG[:2] + app1 + TINY_JPEG[2:])
    assert cleaned[:2] == b"\xff\xd8"
    assert b"Exif" not in cleaned
