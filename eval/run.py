"""Runner d'evaluation.

Pour chaque (config de defense, modele, scenario, repetition) : reinitialise
l'environnement, pose l'injection, rejoue l'agent, applique les checks, ecrit une ligne CSV.
Mesure aussi les taches legitimes seules (utilite sans attaque).

Exemples :
    python -m eval.run --config none
    python -m eval.run --config D3+D4 --reps 3
    python -m eval.run --ablation --out results/ablation.csv
    python -m eval.run --ablation --quick            # suite reduite (CI)
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from agent.config import ABLATION_LABELS, DefenseConfig
from agent.core import run_episode
from agent.models import estimate_cost_usd, model_name, resolve_provider
from mcp_servers.common import reset_environment
from mcp_servers.toolbox import Toolbox

from .checks import run_check
from .scenarios import apply_injection, load_attacks, load_tasks

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["scenario", "category", "vector", "config", "model", "model_name", "rep",
          "attack_success", "utility", "tokens", "latency_ms", "confirmations", "cost_usd", "trace_id"]


def run_one(provider: str, label: str, defenses: DefenseConfig, task: dict,
            scenario: dict | None, rep: int) -> dict:
    env = reset_environment()
    if scenario:
        apply_injection(env, scenario)
    toolbox = Toolbox(env, defenses, task)
    episode = run_episode(task, toolbox, provider)

    utility = run_check(task["success_check"], env, episode)
    m = toolbox.metrics
    row = {
        "config": label, "model": provider, "model_name": model_name(provider), "rep": rep,
        "utility": int(utility), "tokens": m.tokens, "latency_ms": round(m.latency_ms, 2),
        "confirmations": m.confirmations, "cost_usd": estimate_cost_usd(provider, m.tokens),
        "trace_id": "",
    }
    if scenario:
        attack_success = run_check(scenario["success_check"], env, episode)
        row.update({"scenario": scenario["id"], "category": scenario["category"],
                    "vector": scenario["vector"], "attack_success": int(attack_success)})
    else:
        row.update({"scenario": f"legit:{task['id']}", "category": "legit",
                    "vector": "", "attack_success": ""})
    return row


def run_matrix(configs: list[str], provider: str, reps: int, human: str,
               attacks: list[dict], tasks: dict[str, dict], budget: float) -> list[dict]:
    rows: list[dict] = []
    total_cost = 0.0
    for label in configs:
        defenses = DefenseConfig.from_label(label, human_profile=human)
        for task in tasks.values():  # utilite sans attaque
            for rep in range(reps):
                row = run_one(provider, label, defenses, task, None, rep)
                rows.append(row)
                total_cost += row["cost_usd"]
        for sc in attacks:  # scenarios d'attaque
            task = tasks[sc["user_task"]]
            for rep in range(reps):
                row = run_one(provider, label, defenses, task, sc, rep)
                rows.append(row)
                total_cost += row["cost_usd"]
                if budget > 0 and total_cost > budget:
                    print(f"[budget] plafond {budget} USD atteint, arret anticipe.")
                    return rows
    return rows


def write_csv(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _summary(rows: list[dict]) -> None:
    attacks = [r for r in rows if r["attack_success"] != ""]
    by_config: dict[str, list[int]] = {}
    util_by_config: dict[str, list[int]] = {}
    for r in rows:
        if r["attack_success"] != "":
            by_config.setdefault(r["config"], []).append(int(r["attack_success"]))
        else:
            util_by_config.setdefault(r["config"], []).append(int(r["utility"]))
    print("\n=== Resume (par configuration) ===")
    print(f"{'config':<10} {'ASR':>7} {'utilite':>9}")
    for cfg in by_config:
        asr = 100 * sum(by_config[cfg]) / len(by_config[cfg])
        util = util_by_config.get(cfg, [])
        util_pct = 100 * sum(util) / len(util) if util else float("nan")
        print(f"{cfg:<10} {asr:>6.1f}% {util_pct:>8.1f}%")
    print(f"\nRuns d'attaque : {len(attacks)} | total lignes : {len(rows)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="MCP Red-Team Lab -- runner d'eval")
    ap.add_argument("--config", default="none", help="label de defense (none, D1, D3+D4, all, all+D6)")
    ap.add_argument("--ablation", action="store_true", help="toutes les configs de l'ablation")
    ap.add_argument("--model", default=os.getenv("MODEL_PROVIDER", "mock"), help="mock | anthropic | ollama")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--human", default="attentive", choices=["attentive", "tired"])
    ap.add_argument("--quick", action="store_true", help="suite reduite (CI)")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    provider = resolve_provider(args.model)
    tasks = load_tasks()
    attacks = load_attacks()

    if args.ablation:
        configs = ["none", "all"] if args.quick else ABLATION_LABELS
    else:
        configs = [args.config]
    if args.quick:
        attacks = attacks[:5]

    budget = float(os.getenv("BUDGET_USD", "0") or 0)
    print(f"Provider={provider} ({model_name(provider)}) | configs={configs} | "
          f"attaques={len(attacks)} | taches={len(tasks)} | reps={args.reps}")

    rows = run_matrix(configs, provider, args.reps, args.human, attacks, tasks, budget)
    _summary(rows)

    if args.out:
        write_csv(rows, args.out)
        print(f"\nCSV ecrit : {args.out}")


if __name__ == "__main__":
    main()
