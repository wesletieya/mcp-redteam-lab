"""Point d'entree unifie : choisit le bon executeur selon le provider."""

from __future__ import annotations

from mcp_servers.toolbox import Toolbox

from .mock_agent import EpisodeResult
from .mock_agent import run_episode as _run_mock


def get_runner(provider: str):
    if provider == "mock":
        return _run_mock
    if provider == "anthropic":
        from .graph import run_episode_anthropic
        return run_episode_anthropic
    if provider == "ollama":
        from .graph import run_episode_ollama
        return run_episode_ollama
    raise ValueError(f"Provider non supporte : {provider}")


def run_episode(task: dict, toolbox: Toolbox, provider: str = "mock") -> EpisodeResult:
    return get_runner(provider)(task, toolbox)
