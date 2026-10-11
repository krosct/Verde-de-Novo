"""Step-by-step analysis: gate -> species -> parts -> per-part observations -> rules."""

from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

from .catalog import OBSERVATIONS, PART_LABELS, PARTS, SPECIES, SpeciesProfile
from .decision import care_payload, condition_payload, decide
from .vendor import Box, SpeciesGuess, VisionVendor

MIN_OBSERVATION_CONFIDENCE = 0.5
CROP_PADDING = 0.05
NEUTRAL_OBSERVATIONS = frozenset({"leaf_healthy", "stem_healthy", "soil_ok", "roots_healthy"})

QUALITY_MESSAGES: dict[str, str] = {
    "dark": "A foto ficou escura. Tente perto de uma janela ou com mais luz.",
    "blurry": "A foto ficou tremida. Apoie o celular e tente de novo.",
    "too_far": "A planta ficou pequena na foto. Chegue um pouco mais perto.",
}

NOT_PLANT_MESSAGE = "Não encontrei uma planta nesta foto. Tente de novo com a planta inteira aparecendo."
NO_PARTS_MESSAGE = "Não consegui ver as partes da planta. Tente uma foto com folhas, caule e terra aparecendo."
UNKNOWN_SPECIES_NOTE = "Não tenho certeza da espécie, então as dicas de cuidado são gerais."
HEALTHY_MESSAGE = "Não encontrei sinais claros de problema. Veja abaixo como ajudar a planta a crescer ainda mais."
WEAK_SIGNS_MESSAGE = "Vi alguns sinais, mas nada claro o bastante para apontar uma causa. Fique de olho e veja os cuidados abaixo."
CONDITIONS_MESSAGE = "Encontrei alguns pontos de atenção. Veja o que fazer em cada um."


class InvalidImage(ValueError):
    pass


def load_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as error:
        raise InvalidImage(str(error)) from error
    return image.convert("RGB")


def crop(image: Image.Image, box: Box) -> bytes:
    width, height = image.size
    left = max(0.0, box.x - CROP_PADDING) * width
    top = max(0.0, box.y - CROP_PADDING) * height
    right = min(1.0, box.x + box.width + CROP_PADDING) * width
    bottom = min(1.0, box.y + box.height + CROP_PADDING) * height
    if right - left < 1 or bottom - top < 1:
        region = image
    else:
        region = image.crop((round(left), round(top), round(right), round(bottom)))
    buffer = io.BytesIO()
    region.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def empty_response(status: str, message: str, *, ok: bool = True, retry: bool = True) -> dict[str, object]:
    return {
        "ok": ok,
        "status": status,
        "message": message,
        "species": None,
        "alternatives": [],
        "parts": [],
        "conditions": [],
        "care": [],
        "is_diagnosis": False,
        "retry": retry,
    }


def species_payload(guess: SpeciesGuess, known: bool) -> dict[str, object]:
    return {
        "id": guess.species_id if known else None,
        "common_name": guess.common_name,
        "scientific_name": guess.scientific_name,
        "confidence": round(float(guess.confidence), 2),
        "known": known,
    }


def analyze(data: bytes, vendor: VisionVendor, threshold: float) -> dict[str, object]:
    image = load_image(data)

    gate = vendor.check_plant(data)
    if not gate.is_plant or gate.confidence < threshold:
        return empty_response("not_plant", NOT_PLANT_MESSAGE)
    if gate.quality in QUALITY_MESSAGES:
        return empty_response("bad_image", QUALITY_MESSAGES[gate.quality])

    guesses = sorted(vendor.identify_species(data), key=lambda guess: -guess.confidence)
    top = guesses[0] if guesses and guesses[0].confidence >= threshold else None
    profile: SpeciesProfile | None = SPECIES.get(top.species_id or "") if top else None
    species_id = top.species_id if profile else None

    regions = {}
    for region in vendor.locate_parts(data):
        if region.part in PARTS and region.confidence >= threshold:
            current = regions.get(region.part)
            if current is None or region.confidence > current.confidence:
                regions[region.part] = region
    if not regions:
        return empty_response("bad_image", NO_PARTS_MESSAGE)

    ordered_parts = [part for part in PARTS if part in regions]
    crops = {part: crop(image, regions[part].box) for part in ordered_parts}
    with ThreadPoolExecutor(max_workers=len(ordered_parts)) as pool:
        futures = {part: pool.submit(vendor.analyze_part, crops[part], part, species_id) for part in ordered_parts}
        raw_findings = {part: futures[part].result() for part in ordered_parts}

    findings: dict[str, float] = {}
    parts_payload = []
    for part in ordered_parts:
        observations = []
        for finding in sorted(raw_findings[part], key=lambda item: -item.confidence):
            entry = OBSERVATIONS.get(finding.code)
            if entry is None or entry[0] != part or finding.confidence < MIN_OBSERVATION_CONFIDENCE:
                continue
            confidence = round(float(finding.confidence), 2)
            observations.append({"code": finding.code, "label": entry[1], "confidence": confidence})
            if finding.code not in NEUTRAL_OBSERVATIONS:
                findings[finding.code] = max(findings.get(finding.code, 0.0), confidence)
        parts_payload.append({"part": part, "label": PART_LABELS[part], "observations": observations})

    conditions = decide(findings, profile, threshold)
    if conditions:
        message = CONDITIONS_MESSAGE
    elif findings:
        message = WEAK_SIGNS_MESSAGE
    else:
        message = HEALTHY_MESSAGE
    if top is None or profile is None:
        message = f"{message} {UNKNOWN_SPECIES_NOTE}"

    response = empty_response("analyzed", message, retry=False)
    response.update(
        {
            "species": species_payload(top, profile is not None) if top else None,
            "alternatives": [
                species_payload(guess, guess.species_id in SPECIES) for guess in guesses if guess is not top
            ][:2],
            "parts": parts_payload,
            "conditions": [condition_payload(result) for result in conditions],
            "care": care_payload(profile),
        }
    )
    return response
