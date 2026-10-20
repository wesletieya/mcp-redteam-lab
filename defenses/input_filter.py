"""D2 -- Filtre d'entree (classifieur d'injection).

Applique a chaque sortie d'outil avant qu'elle n'atteigne l'agent. Dans ce labo, le
classifieur est un detecteur heuristique (regex ponderees) pour rester hors-ligne et
deterministe. En production, remplacer `score()` par un appel a Prompt-Guard / un modele
DeBERTa fine-tune ; l'interface (texte -> score dans [0,1]) reste la meme.

Cout a mesurer : latence et faux positifs (contenu benin masque a tort)."""

from __future__ import annotations

import re

# Motifs typiques d'instruction injectee (FR + EN), ponderes.
_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\[\[\s*CMD\s*:", re.IGNORECASE), 0.9),
    (re.compile(r"\bignore[sz]?\b.{0,20}\b(previous|precedent|instructions|consignes)\b", re.IGNORECASE), 0.8),
    (re.compile(r"\b(system|systeme)\s*:", re.IGNORECASE), 0.4),
    (re.compile(r"\b(send|envoie[rz]?|forward|transfer[ez]?|exfiltr)\w*\b.{0,30}\b(email|canary|key|cle|secret)\b", re.IGNORECASE), 0.7),
    (re.compile(r"\b(close|ferme[rz]?|delete|supprime[rz]?|update|modifie[rz]?)\b.{0,20}\b(ticket|config|mission)\b", re.IGNORECASE), 0.6),
    (re.compile(r"\byou must\b|\btu dois\b|\bimperatif\b", re.IGNORECASE), 0.4),
    (re.compile(r"CNRY-[0-9a-fA-F]{8}", re.IGNORECASE), 0.5),
]

DEFAULT_THRESHOLD = 0.5
LATENCY_MS = 8  # cout de latence simule par appel


def score(text: str) -> float:
    """Probabilite ~ que le texte contienne une instruction injectee (max des motifs)."""
    return max((w for pat, w in _PATTERNS if pat.search(text)), default=0.0)


def sanitize(text: str, threshold: float = DEFAULT_THRESHOLD) -> tuple[str, bool]:
    """Retourne (texte_nettoye, detecte). Si suspect, masque les spans dangereux."""
    detected = score(text) >= threshold
    if not detected:
        return text, False
    cleaned = text
    for pat, _w in _PATTERNS:
        cleaned = pat.sub("[CONTENU SUSPECT MASQUE PAR D2]", cleaned)
    return cleaned, True
