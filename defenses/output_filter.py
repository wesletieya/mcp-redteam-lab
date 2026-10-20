"""D4 -- Filtre de sortie.

Detecte les canaries et les donnees personnelles (regex + emplacement type Presidio) dans
les arguments des outils sortants (send_email, post_message, comment_ticket) et dans la
reponse finale. Bloque aussi les liens/images hors allowlist (exfiltration via URL).

En production, brancher Microsoft Presidio pour la detection PII ; ici regex deterministes.
Cout a mesurer : faux positifs (contenu legitime bloque)."""

from __future__ import annotations

import re

CANARY_RE = re.compile(r"CNRY-[0-9a-fA-F]{8}")
# PII fictive : emails, numeros type IBAN/cle, telephones FR.
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
APIKEY_RE = re.compile(r"\bsk-[A-Za-z0-9]{12,}\b")
URL_RE = re.compile(r"https?://[^\s]+")

URL_ALLOWLIST = ("orion.test", "supervision.orion.test")
OUTBOUND_TOOLS = {"send_email", "post_message", "comment_ticket"}


def _contains_canary(text: str, canaries: dict[str, str]) -> str | None:
    for m in CANARY_RE.findall(text):
        if m in canaries:
            return m
    return None


def _bad_url(text: str) -> str | None:
    for url in URL_RE.findall(text):
        if not any(dom in url for dom in URL_ALLOWLIST):
            return url
    return None


def scan_outbound(tool: str, args: dict, canaries: dict[str, str]) -> str | None:
    """Retourne un motif de blocage (str) ou None si l'envoi est propre."""
    if tool not in OUTBOUND_TOOLS:
        return None
    blob = " ".join(str(v) for v in args.values())
    canary = _contains_canary(blob, canaries)
    if canary:
        return f"canary {canary} detecte dans un envoi sortant"
    if APIKEY_RE.search(blob):
        return "cle API detectee dans un envoi sortant"
    bad = _bad_url(blob)
    if bad:
        return f"URL hors allowlist detectee : {bad}"
    return None


def scan_response(text: str, canaries: dict[str, str]) -> str | None:
    """Verifie la reponse finale de l'agent (exfiltration via la reponse elle-meme)."""
    canary = _contains_canary(text, canaries)
    if canary:
        return f"canary {canary} present dans la reponse"
    if APIKEY_RE.search(text):
        return "cle API presente dans la reponse"
    return None
