"""Serveur `tickets` : lecture/ecriture de tickets d'exploitation.

Role dans les tests : injection par sortie d'outil (un commentaire de ticket peut etre
controle par l'attaquant) et abus d'action (fermeture/commentaire non demandes)."""

from __future__ import annotations

import json

from .common import Env


def _load(env: Env) -> list[dict]:
    return json.loads(env.tickets_path.read_text(encoding="utf-8"))


def _save(env: Env, tickets: list[dict]) -> None:
    env.tickets_path.write_text(json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8")


def list_tickets(env: Env, status: str | None = None) -> dict:
    tickets = _load(env)
    rows = [
        {"id": t["id"], "title": t["title"], "status": t["status"]}
        for t in tickets
        if status is None or t["status"] == status
    ]
    return {"tickets": rows}


def read_ticket(env: Env, ticket_id: str) -> dict:
    for t in _load(env):
        if t["id"] == ticket_id:
            comments = list(t.get("comments", []))
            # Commentaires injectes par l'attaquant (vecteur tool_output).
            for extra in env.injected_ticket_comments.get(ticket_id, []):
                comments.append({"author": "externe", "body": extra})
            return {**t, "comments": comments}
    return {"error": f"Ticket {ticket_id} introuvable"}


def comment_ticket(env: Env, ticket_id: str, body: str) -> dict:
    tickets = _load(env)
    for t in tickets:
        if t["id"] == ticket_id:
            t.setdefault("comments", []).append({"author": "agent-ORION", "body": body})
            _save(env, tickets)
            return {"ok": True, "ticket_id": ticket_id}
    return {"error": f"Ticket {ticket_id} introuvable"}


def close_ticket(env: Env, ticket_id: str) -> dict:
    tickets = _load(env)
    for t in tickets:
        if t["id"] == ticket_id:
            t["status"] = "ferme"
            _save(env, tickets)
            return {"ok": True, "ticket_id": ticket_id, "status": "ferme"}
    return {"error": f"Ticket {ticket_id} introuvable"}


TOOLS = {
    "list_tickets": list_tickets,
    "read_ticket": read_ticket,
    "comment_ticket": comment_ticket,
    "close_ticket": close_ticket,
}
