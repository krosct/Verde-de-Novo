from __future__ import annotations

from server.config import build_config

ENV_KEYS = (
    "PORT",
    "HOST",
    "VISION_PROVIDER",
    "PORT_SEARCH",
    "RELOAD",
    "CONFIDENCE_THRESHOLD",
)


def clear_env(monkeypatch) -> None:
    for name in ENV_KEYS:
        monkeypatch.delenv(name, raising=False)


def test_defaults_are_stable(monkeypatch) -> None:
    clear_env(monkeypatch)
    config = build_config([])
    assert config.port == 8000
    assert config.port_search is True
    assert config.reload is False
    assert config.vision_provider == "stub"


def test_cli_overrides_and_flags(monkeypatch) -> None:
    clear_env(monkeypatch)
    config = build_config(
        ["--port", "9123", "--no-port-search", "--reload", "--confidence-threshold", "0.9"]
    )
    assert config.port == 9123
    assert config.port_search is False
    assert config.reload is True
    assert config.confidence_threshold == 0.9


def test_environment_used_without_cli(monkeypatch) -> None:
    clear_env(monkeypatch)
    monkeypatch.setenv("PORT", "9200")
    monkeypatch.setenv("PORT_SEARCH", "false")
    config = build_config([])
    assert config.port == 9200
    assert config.port_search is False
