"""Schemas JSON des outils, pour la boucle tool-use des providers LLM reels."""

from __future__ import annotations

SCHEMAS: dict[str, dict] = {
    "search_docs": {"query": "string", "k": "integer"},
    "list_tickets": {"status": "string"},
    "read_ticket": {"ticket_id": "string"},
    "comment_ticket": {"ticket_id": "string", "body": "string"},
    "close_ticket": {"ticket_id": "string"},
    "query_db": {"sql": "string"},
    "send_email": {"to": "string", "subject": "string", "body": "string"},
    "post_message": {"channel": "string", "body": "string"},
    "update_config": {"mission_id": "string", "key": "string", "value": "string"},
    "read_config": {"mission_id": "string"},
    "weather_lookup": {"station": "string"},
}

REQUIRED: dict[str, list[str]] = {
    "search_docs": ["query"],
    "read_ticket": ["ticket_id"],
    "comment_ticket": ["ticket_id", "body"],
    "close_ticket": ["ticket_id"],
    "query_db": ["sql"],
    "send_email": ["to", "subject", "body"],
    "post_message": ["channel", "body"],
    "update_config": ["mission_id", "key", "value"],
    "read_config": ["mission_id"],
    "weather_lookup": ["station"],
}


def anthropic_tools(available: set[str], descriptions: dict[str, str]) -> list[dict]:
    tools = []
    for name in sorted(available):
        if name not in SCHEMAS:
            continue
        props = {k: {"type": t} for k, t in SCHEMAS[name].items()}
        tools.append({
            "name": name,
            "description": descriptions.get(name, name),
            "input_schema": {"type": "object", "properties": props,
                             "required": REQUIRED.get(name, [])},
        })
    return tools
