"""Vision steps behind one adapter. Each step answers one small question with fixed codes."""

from __future__ import annotations

import hashlib
from typing import NamedTuple, Protocol

from .catalog import OBSERVATIONS, PARTS, SPECIES
from .config import Config

IMAGE_QUALITIES: tuple[str, ...] = ("ok", "dark", "blurry", "too_far")


class GateResult(NamedTuple):
    is_plant: bool
    confidence: float
    quality: str


class SpeciesGuess(NamedTuple):
    species_id: str | None
    common_name: str
    scientific_name: str
    confidence: float


class Box(NamedTuple):
    x: float
    y: float
    width: float
    height: float


class PartRegion(NamedTuple):
    part: str
    box: Box
    confidence: float


class Finding(NamedTuple):
    code: str
    confidence: float


class VisionVendor(Protocol):
    def check_plant(self, image: bytes) -> GateResult: ...

    def identify_species(self, image: bytes) -> list[SpeciesGuess]: ...

    def locate_parts(self, image: bytes) -> list[PartRegion]: ...

    def analyze_part(self, crop: bytes, part: str, species_id: str | None) -> list[Finding]: ...


def _digest(*chunks: bytes) -> bytes:
    hasher = hashlib.sha256()
    for chunk in chunks:
        hasher.update(chunk)
    return hasher.digest()


def _confidence(byte: int, low: float = 0.5, high: float = 0.95) -> float:
    return round(low + (byte / 255) * (high - low), 2)


_STUB_BOXES: dict[str, Box] = {
    "leaf": Box(0.15, 0.05, 0.7, 0.5),
    "stem": Box(0.4, 0.45, 0.2, 0.3),
    "soil": Box(0.2, 0.7, 0.6, 0.15),
    "roots": Box(0.25, 0.85, 0.5, 0.15),
}

_STUB_PART_ODDS: dict[str, int] = {"leaf": 256, "stem": 180, "soil": 150, "roots": 26}


class StubVendor:
    """Deterministic offline vendor: same photo, same answers. It does not look at the plant."""

    def check_plant(self, image: bytes) -> GateResult:
        return GateResult(True, 0.9, "ok")

    def identify_species(self, image: bytes) -> list[SpeciesGuess]:
        digest = _digest(image, b"species")
        ids = list(SPECIES)
        guesses = []
        for rank in range(3):
            species_id = ids[digest[rank] % len(ids)]
            if any(guess.species_id == species_id for guess in guesses):
                continue
            profile = SPECIES[species_id]
            confidence = _confidence(digest[10 + rank], 0.55, 0.95) / (rank + 1)
            guesses.append(SpeciesGuess(species_id, profile.common_name, profile.scientific_name, round(confidence, 2)))
        return guesses

    def locate_parts(self, image: bytes) -> list[PartRegion]:
        digest = _digest(image, b"parts")
        return [
            PartRegion(part, _STUB_BOXES[part], _confidence(digest[index + 8]))
            for index, part in enumerate(PARTS)
            if digest[index] < _STUB_PART_ODDS[part]
        ]

    def analyze_part(self, crop: bytes, part: str, species_id: str | None) -> list[Finding]:
        digest = _digest(crop, part.encode())
        codes = [code for code, (owner, _) in OBSERVATIONS.items() if owner == part]
        picked = {codes[digest[0] % len(codes)], codes[digest[1] % len(codes)]}
        return [Finding(code, _confidence(digest[2 + index], 0.45, 0.95)) for index, code in enumerate(sorted(picked))]


def get_vendor(config: Config) -> VisionVendor:
    return StubVendor()
