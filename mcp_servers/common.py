"""Primitives partagees : chemins, journal d'audit, environnement reinitialisable."""

from __future__ import annotations

import json
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "data" / "seed"
CANARIES_PATH = ROOT / "data" / "canaries.json"
RUNTIME_DIR = ROOT / "runtime"


class AuditLogger:
    """Ecrit une ligne JSON par appel d'outil : la verite terrain pour mesurer."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def log(self, server: str, tool: str, args: dict[str, Any], result: Any,
            blocked_by: str | None = None) -> None:
        entry = {
            "ts": round(time.time(), 3),
            "server": server,
            "tool": tool,
            "args": args,
            "result": _summarize(result),
            "blocked_by": blocked_by,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]


def _summarize(result: Any) -> Any:
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
    return text if len(text) <= 500 else text[:500] + "...<truncated>"


@dataclass
class Env:
    """Etat d'un run : chemins runtime + donnees chargees + injections eventuelles."""

    runtime_dir: Path
    audit: AuditLogger
    canaries: dict[str, str] = field(default_factory=dict)
    # Injections posees par le runner avant un scenario d'attaque.
    poisoned_docs: dict[str, str] = field(default_factory=dict)      # doc_id -> texte injecte ajoute
    injected_ticket_comments: dict[str, list[str]] = field(default_factory=dict)  # ticket_id -> commentaires
    rogue_enabled: bool = False
    rogue_description_payload: str = ""

    @property
    def outbox_path(self) -> Path:
        return self.runtime_dir / "outbox.jsonl"

    @property
    def tickets_path(self) -> Path:
        return self.runtime_dir / "tickets.json"

    @property
    def configs_path(self) -> Path:
        return self.runtime_dir / "mission_configs.json"

    @property
    def db_path(self) -> Path:
        return self.runtime_dir / "lab.db"

    @property
    def docs_dir(self) -> Path:
        return self.runtime_dir / "docs"

    def read_outbox(self) -> list[dict[str, Any]]:
        if not self.outbox_path.exists():
            return []
        return [json.loads(line) for line in self.outbox_path.read_text(encoding="utf-8").splitlines() if line]

    def db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


def reset_environment(runtime_dir: Path = RUNTIME_DIR) -> Env:
    """Recopie les donnees seed dans runtime/ et vide les journaux. Appele avant chaque run."""
    if not SEED_DIR.exists():
        raise FileNotFoundError(
            f"Donnees seed absentes ({SEED_DIR}). Lancez `make data` (python -m data.generate)."
        )
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(SEED_DIR / "lab.db", runtime_dir / "lab.db")
    shutil.copy(SEED_DIR / "tickets.json", runtime_dir / "tickets.json")
    shutil.copy(SEED_DIR / "mission_configs.json", runtime_dir / "mission_configs.json")
    shutil.copytree(SEED_DIR / "docs", runtime_dir / "docs")
    (runtime_dir / "outbox.jsonl").write_text("", encoding="utf-8")

    canaries = json.loads(CANARIES_PATH.read_text(encoding="utf-8")) if CANARIES_PATH.exists() else {}
    audit = AuditLogger(runtime_dir / "audit.jsonl")
    return Env(runtime_dir=runtime_dir, audit=audit, canaries=canaries)
