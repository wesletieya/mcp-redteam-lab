"""D6 -- Plan-then-execute.

Un planificateur qui ne voit QUE la demande utilisateur et la liste d'outils fige la
sequence d'appels autorises. L'executeur remplit les arguments mais ne peut pas ajouter
d'appel qui ne figure pas dans le plan. Une instruction injectee dans une sortie d'outil
ne peut donc pas introduire un nouvel appel (ex: un send_email surprise).

Inspire des "Design Patterns for Securing LLM Agents against Prompt Injections" (2025) et
de CaMeL (Google DeepMind, 2025).

Cout a mesurer : utilite (plans trop rigides) et latence (etape de planification)."""

from __future__ import annotations


def build_plan(task: dict) -> list[str]:
    """Le plan = la sequence d'outils derivee de la seule demande (champ `plan` de la tache)."""
    return [step["tool"] for step in task.get("plan", [])]


def call_allowed(plan: list[str], already_called: list[str], tool: str) -> bool:
    """Autorise `tool` seulement s'il reste une occurrence prevue dans le plan."""
    planned_count = plan.count(tool)
    done_count = already_called.count(tool)
    return done_count < planned_count
