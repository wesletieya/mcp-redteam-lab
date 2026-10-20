"""Chargement des taches/attaques et pose des injections dans l'environnement."""

from __future__ import annotations

from pathlib import Path

import yaml

from mcp_servers.common import Env

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"
ATTACKS_DIR = ROOT / "attacks"


def _load_yaml_dir(directory: Path) -> list[dict]:
    items: list[dict] = []
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items.extend(data)
        elif isinstance(data, dict):
            items.append(data)
    return items


def load_tasks() -> dict[str, dict]:
    return {t["id"]: t for t in _load_yaml_dir(TASKS_DIR)}


def load_attacks() -> list[dict]:
    return _load_yaml_dir(ATTACKS_DIR)


def apply_injection(env: Env, scenario: dict) -> None:
    """Pose le payload de l'attaquant la ou la tache legitime ira lire."""
    vector = scenario["vector"]
    template = scenario["template"]
    placement = scenario.get("placement", {}) or {}

    if vector == "doc":
        env.poisoned_docs[placement["doc_id"]] = template
    elif vector == "tool_output":
        ticket_id = placement["ticket_id"]
        env.injected_ticket_comments.setdefault(ticket_id, []).append(template)
    elif vector == "tool_description":
        env.rogue_enabled = True
        env.rogue_description_payload = template
    else:
        raise ValueError(f"Vecteur inconnu : {vector}")
