"""Abstraction de modele : bascule entre `mock`, `anthropic` (API) et `ollama` (local).

Le choix se fait par la variable d'environnement MODEL_PROVIDER (ou l'option --model).
Seul `mock` est garanti sans dependance ni cle (utilise par les tests et la CI)."""

from __future__ import annotations

import os

SUPPORTED = ("mock", "anthropic", "ollama")

# Cout indicatif par 1M tokens (USD) pour estimer la colonne cout (a ajuster).
PRICE_PER_MTOK = {
    "anthropic": 1.0,   # ordre de grandeur d'un petit modele API
    "ollama": 0.0,      # local
    "mock": 0.0,
}


def resolve_provider(cli_value: str | None = None) -> str:
    provider = (cli_value or os.getenv("MODEL_PROVIDER", "mock")).lower()
    if provider not in SUPPORTED:
        raise ValueError(f"Provider inconnu : {provider}. Choisir parmi {SUPPORTED}.")
    return provider


def model_name(provider: str) -> str:
    if provider == "anthropic":
        return os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
    if provider == "ollama":
        return os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    return "mock-deterministic"


def estimate_cost_usd(provider: str, tokens: int) -> float:
    return round(PRICE_PER_MTOK.get(provider, 0.0) * tokens / 1_000_000, 6)
