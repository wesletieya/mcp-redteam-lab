"""Toolbox : l'agent ne parle jamais directement aux serveurs.

Chaque appel traverse les gardes sortantes (D3 moindre privilege, D5 confirmation humaine,
D4 filtre de sortie, D6 plan fige) ; chaque sortie d'outil traverse les transformations
entrantes (D2 filtre d'entree, D1 spotlighting) avant d'atteindre l'agent. Tout est
journalise dans audit.jsonl."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field

from agent.config import DefenseConfig
from defenses import hitl, input_filter, output_filter, planner, spotlighting
from defenses.least_privilege import Policy, policy_for

from . import config_server, db_server, docs_server, messaging_server, rogue_server, tickets_server
from .common import Env

_REGISTRY = {}
for _mod in (docs_server, tickets_server, db_server, messaging_server, config_server, rogue_server):
    for _name, _fn in _mod.TOOLS.items():
        _REGISTRY[_name] = (_mod.__name__.split(".")[-1].replace("_server", ""), _fn)

# Cout approximatif (tokens) d'un appel d'outil de base, pour la colonne cout.
BASE_TOKENS_PER_CALL = 120


@dataclass
class CallResult:
    tool: str
    ok: bool
    result: dict
    blocked_by: str | None = None
    observation: str = ""
    spotlighted: bool = False


@dataclass
class Metrics:
    tokens: int = 0
    latency_ms: float = 0.0
    confirmations: int = 0
    d2_detections: int = 0
    blocks: dict[str, int] = field(default_factory=dict)

    def add_block(self, defense: str) -> None:
        self.blocks[defense] = self.blocks.get(defense, 0) + 1


class Toolbox:
    def __init__(self, env: Env, defenses: DefenseConfig, task: dict):
        self.env = env
        self.defenses = defenses
        self.task = task
        self.policy: Policy = policy_for(task, defenses.d3_least_privilege)
        self.plan: list[str] = planner.build_plan(task) if defenses.d6_planner else []
        self.called: list[str] = []
        self.metrics = Metrics()

    # --- Outils exposes (D3 restreint la liste presentee a l'agent) ---
    def available_tools(self) -> set[str]:
        if self.defenses.d3_least_privilege:
            return set(self.policy.allowed_tools)
        return set(_REGISTRY.keys())

    def rogue_description(self) -> str:
        return rogue_server.tool_description(self.env)

    # --- Appel sortant (gardes avant execution) ---
    def call(self, tool: str, **args) -> CallResult:
        self.metrics.tokens += BASE_TOKENS_PER_CALL

        if tool not in _REGISTRY:
            return self._blocked(tool, args, None, {"error": f"Outil inconnu : {tool}"})

        # Arguments hors schema (frequent avec un vrai LLM) : erreur renvoyee a l'agent.
        try:
            inspect.signature(_REGISTRY[tool][1]).bind(self.env, **args)
        except TypeError as exc:
            return self._blocked(tool, args, None, {"error": f"Arguments invalides pour {tool} : {exc}"})

        # D6 : plan fige.
        if self.defenses.d6_planner and not planner.call_allowed(self.plan, self.called, tool):
            return self._blocked(tool, args, "D6",
                                 {"error": "Appel hors plan fige (plan-then-execute)."})

        # D3 : outil expose ? action dans le scope ?
        if self.defenses.d3_least_privilege:
            if not self.policy.tool_allowed(tool):
                return self._blocked(tool, args, "D3",
                                     {"error": f"Outil '{tool}' non expose pour cette tache."})
            refusal = self.policy.check_action(tool, args)
            if refusal:
                return self._blocked(tool, args, "D3", {"error": refusal})

        # D5 : confirmation humaine avant action sensible.
        if self.defenses.d5_hitl and hitl.requires_confirmation(tool):
            self.metrics.confirmations += 1
            if not hitl.human_approves(tool, args, self.task, self.defenses.human_profile):
                return self._blocked(tool, args, "D5",
                                     {"error": "Action refusee par l'operateur (confirmation)."})

        # D4 : filtre de sortie sur les arguments sortants.
        if self.defenses.d4_output_filter:
            reason = output_filter.scan_outbound(tool, args, self.env.canaries)
            if reason:
                return self._blocked(tool, args, "D4", {"error": f"Envoi bloque par D4 : {reason}"})

        # Execution reelle, avec arguments durcis par D3 si besoin.
        result = self._execute(tool, args)
        self.called.append(tool)
        self.env.audit.log(_REGISTRY[tool][0], tool, args, result, blocked_by=None)
        return CallResult(tool=tool, ok="error" not in result, result=result)

    def _execute(self, tool: str, args: dict) -> dict:
        _server, fn = _REGISTRY[tool]
        kwargs = dict(args)
        if tool == "query_db" and self.defenses.d3_least_privilege:
            kwargs["hidden_tables"] = self.policy.hidden_tables
        if tool == "send_email" and self.defenses.d3_least_privilege:
            kwargs["allowlist"] = self.policy.email_allowlist
        return fn(self.env, **kwargs)

    def _blocked(self, tool: str, args: dict, defense: str | None, result: dict) -> CallResult:
        if defense:
            self.metrics.add_block(defense)
        self.env.audit.log(_REGISTRY.get(tool, ("?", None))[0], tool, args, result, blocked_by=defense)
        return CallResult(tool=tool, ok=False, result=result, blocked_by=defense)

    # --- Transformation entrante (sortie d'outil -> observation agent) ---
    def observe(self, result: dict) -> tuple[str, bool]:
        text = json.dumps(result, ensure_ascii=False)

        if self.defenses.d4_output_filter:  # masquer les canaries lus (fuite indirecte)
            for canary in self.env.canaries:
                text = text.replace(canary, "[CANARY-REDACTED]")

        if self.defenses.d2_input_filter:
            self.metrics.latency_ms += input_filter.LATENCY_MS
            text, detected = input_filter.sanitize(text)
            if detected:
                self.metrics.d2_detections += 1

        spotlighted = self.defenses.d1_spotlighting
        if spotlighted:
            self.metrics.tokens += spotlighting.TOKEN_OVERHEAD
            text = spotlighting.wrap(text)
        return text, spotlighted
