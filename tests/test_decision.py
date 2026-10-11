from __future__ import annotations

from server.catalog import CONDITIONS, OBSERVATIONS, SPECIES
from server.decision import CONTRADICTIONS, RULES, decide


def test_rules_only_use_catalog_codes() -> None:
    assert set(RULES) == set(CONDITIONS)
    for weights in RULES.values():
        assert set(weights) <= set(OBSERVATIONS)
    for condition, codes in CONTRADICTIONS.items():
        assert condition in CONDITIONS
        assert set(codes) <= set(OBSERVATIONS)


def test_no_evidence_means_no_conditions() -> None:
    assert decide({}, None, 0.6) == []


def test_weak_single_sign_stays_below_threshold() -> None:
    assert decide({"leaf_drooping": 0.9}, None, 0.6) == []


def test_contradiction_suppresses_condition() -> None:
    codes = [result.code for result in decide({"leaf_yellow_lower": 0.9, "soil_wet": 0.9, "soil_dry": 0.9}, None, 0.6)]
    assert "overwatering" not in codes


def test_species_changes_the_reading() -> None:
    findings = {"leaf_brown_tips": 0.95, "leaf_curling": 0.9}
    fern = [result.code for result in decide(findings, SPECIES["nephrolepis_exaltata"], 0.6)]
    cactus = [result.code for result in decide(findings, SPECIES["cactus"], 0.6)]
    assert "low_humidity" in fern
    assert "low_humidity" not in cactus


def test_sunburn_is_unlikely_for_sun_lovers() -> None:
    findings = {"leaf_scorch": 0.8}
    assert decide(findings, SPECIES["calathea"], 0.6)[0].code == "too_much_sun"
    assert decide(findings, SPECIES["aloe_vera"], 0.6) == []
