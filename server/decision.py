"""Deterministic rules: observations + species profile -> conditions -> suggestions.

Models only report what they see. This module decides, so every answer can be traced to evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import (
    CONDITION_ORDER,
    CONDITIONS,
    HUMIDITY_LABELS,
    LIGHT_LABELS,
    OBSERVATIONS,
    WATER_LABELS,
    SpeciesProfile,
)

RULES: dict[str, dict[str, float]] = {
    "overwatering": {
        "soil_wet": 0.7,
        "leaf_yellow_lower": 0.5,
        "leaf_soft_dark": 0.4,
        "soil_white_mold": 0.4,
        "leaf_drooping": 0.2,
    },
    "underwatering": {
        "soil_pulling_away": 0.7,
        "soil_dry": 0.6,
        "roots_dry": 0.6,
        "leaf_curling": 0.4,
        "leaf_drooping": 0.3,
        "leaf_brown_tips": 0.3,
    },
    "low_light": {
        "stem_leggy": 0.7,
        "stem_leaning": 0.5,
        "leaf_small_new": 0.5,
        "leaf_pale": 0.3,
        "leaf_dark_dull": 0.2,
    },
    "too_much_sun": {"leaf_scorch": 0.8, "leaf_pale": 0.2},
    "low_humidity": {"leaf_brown_tips": 0.6, "leaf_curling": 0.3},
    "fungus": {"leaf_spots_halo": 0.8, "leaf_powdery": 0.8},
    "pest": {"leaf_pests": 0.9, "stem_pests": 0.9},
    "root_rot_risk": {"roots_brown_mushy": 0.9, "stem_soft_base": 0.8},
    "pot_bound": {"roots_circling": 0.8, "soil_roots_surfacing": 0.7},
    "poor_soil": {"soil_compacted": 0.7, "soil_white_mold": 0.4},
    "nutrient_need": {"leaf_yellow_spread": 0.5, "leaf_pale": 0.4},
}

CONTRADICTIONS: dict[str, tuple[str, ...]] = {
    "overwatering": ("soil_dry", "soil_pulling_away", "roots_dry"),
    "underwatering": ("soil_wet", "roots_brown_mushy"),
    "nutrient_need": ("stem_leggy",),
}

CONTRADICTION_FACTOR = 0.3

GENERIC_CARE: tuple[tuple[str, str, str], ...] = (
    ("light", "Luz", "A maioria das plantas de casa cresce mais com bastante luz indireta, perto de uma janela."),
    ("water", "Rega", "Regue quando os primeiros centímetros da terra estiverem secos, sem deixar água no pratinho."),
    ("humidity", "Umidade", "Evite deixar a planta na corrente de ar-condicionado ou aquecedor."),
)


@dataclass(frozen=True)
class ConditionResult:
    code: str
    confidence: float
    evidence: tuple[str, ...]


def species_factor(condition: str, profile: SpeciesProfile | None) -> float:
    if profile is None:
        return 0.8 if condition == "low_humidity" else 1.0
    if condition == "overwatering" and profile.water == "low":
        return 1.2
    if condition == "underwatering" and profile.water == "high":
        return 1.2
    if condition == "underwatering" and profile.water == "low":
        return 0.7
    if condition == "low_humidity":
        return {"high": 1.1, "medium": 0.7, "low": 0.3}[profile.humidity]
    if condition == "too_much_sun" and profile.light == "direct":
        return 0.5
    if condition == "low_light" and profile.light in {"direct", "bright_indirect"}:
        return 1.2
    return 1.0


def decide(
    findings: dict[str, float],
    profile: SpeciesProfile | None,
    threshold: float,
) -> list[ConditionResult]:
    results = []
    for condition in CONDITION_ORDER:
        weights = RULES[condition]
        evidence = [code for code in weights if code in findings]
        if not evidence:
            continue
        miss = 1.0
        for code in evidence:
            miss *= 1.0 - weights[code] * findings[code]
        score = (1.0 - miss) * species_factor(condition, profile)
        if any(code in findings for code in CONTRADICTIONS.get(condition, ())):
            score *= CONTRADICTION_FACTOR
        score = min(score, 1.0)
        if score >= threshold:
            ordered = tuple(sorted(evidence, key=lambda code: -weights[code] * findings[code]))
            results.append(ConditionResult(condition, round(score, 2), ordered))
    results.sort(key=lambda item: -item.confidence)
    return results


def condition_payload(result: ConditionResult) -> dict[str, object]:
    condition = CONDITIONS[result.code]
    return {
        "code": result.code,
        "label": condition.label,
        "explanation": condition.explanation,
        "confidence": result.confidence,
        "evidence": [OBSERVATIONS[code][1] for code in result.evidence],
        "suggestions": list(condition.suggestions),
    }


def care_payload(profile: SpeciesProfile | None) -> list[dict[str, str]]:
    if profile is None:
        return [{"topic": topic, "label": label, "text": text} for topic, label, text in GENERIC_CARE]
    return [
        {"topic": "light", "label": "Luz", "text": LIGHT_LABELS[profile.light]},
        {"topic": "water", "label": "Rega", "text": WATER_LABELS[profile.water]},
        {"topic": "humidity", "label": "Umidade", "text": HUMIDITY_LABELS[profile.humidity]},
        {"topic": "growth", "label": "Para crescer mais", "text": profile.growth_tip},
    ]
