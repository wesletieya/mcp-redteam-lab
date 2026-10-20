"""D3 -- Moindre privilege.

Couche de politique autour du noeud outils :
  * seuls les outils necessaires a la tache sont exposes ;
  * la base est en lecture seule et la table `api_keys` est masquee ;
  * allowlist de destinataires pour send_email ;
  * close_ticket limite aux tickets cites par l'utilisateur.

La politique refuse avec un message clair (l'agent peut continuer sa tache au lieu de boucler).
Cout a mesurer : taches legitimes bloquees (faux refus)."""

from __future__ import annotations

from dataclasses import dataclass, field

HIDDEN_TABLES = ("api_keys",)
# Destinataires internes legitimes (bac a sable).
DEFAULT_EMAIL_ALLOWLIST = ("ops@orion.test", "supervision@orion.test")

ALL_TOOLS = {
    "search_docs", "list_tickets", "read_ticket", "comment_ticket", "close_ticket",
    "query_db", "send_email", "post_message", "update_config", "read_config", "weather_lookup",
}
SENSITIVE_TOOLS = {"send_email", "close_ticket", "update_config", "post_message"}


@dataclass
class Policy:
    enabled: bool
    allowed_tools: set[str] = field(default_factory=lambda: set(ALL_TOOLS))
    hidden_tables: tuple[str, ...] = ()
    email_allowlist: tuple[str, ...] | None = None
    close_ticket_allowed: tuple[str, ...] | None = None  # None = pas de restriction

    def tool_allowed(self, tool: str) -> bool:
        return tool in self.allowed_tools

    def check_action(self, tool: str, args: dict) -> str | None:
        """Retourne un message de refus, ou None si l'action est permise."""
        if not self.enabled:
            return None
        if tool == "close_ticket" and self.close_ticket_allowed is not None:
            if args.get("ticket_id") not in self.close_ticket_allowed:
                return (f"Politique moindre privilege : close_ticket autorise uniquement pour "
                        f"{self.close_ticket_allowed}, pas {args.get('ticket_id')}.")
        return None


def policy_for(task: dict, enabled: bool) -> Policy:
    if not enabled:
        return Policy(enabled=False)
    needed = set(task.get("tools_needed", [])) or set(ALL_TOOLS)
    scope = task.get("scope", {})
    recipients = tuple(scope.get("email_recipients", DEFAULT_EMAIL_ALLOWLIST))
    ticket_ids = tuple(scope.get("ticket_ids", [])) or None
    return Policy(
        enabled=True,
        allowed_tools=needed,
        hidden_tables=HIDDEN_TABLES,
        email_allowlist=recipients,
        close_ticket_allowed=ticket_ids,
    )
