"""Serveur `docs` : recherche dans les procedures d'exploitation (RAG simplifie).

Role dans les tests : vecteur d'injection par document (un document du corpus peut
contenir une instruction cachee posee par l'attaquant)."""

from __future__ import annotations

from .common import Env


def _load_docs(env: Env) -> dict[str, str]:
    docs: dict[str, str] = {}
    for p in sorted(env.docs_dir.glob("*.md")):
        docs[p.stem] = p.read_text(encoding="utf-8")
    return docs


def search_docs(env: Env, query: str, k: int = 3) -> dict:
    """Recherche lexicale naive (BM25-like) dans les procedures. Renvoie les k meilleurs extraits."""
    query_terms = {w.lower() for w in query.split() if len(w) > 2}
    docs = _load_docs(env)
    scored: list[tuple[int, str, str]] = []
    for doc_id, text in docs.items():
        body = text
        if doc_id in env.poisoned_docs:  # injection posee par le runner
            body = body + "\n\n" + env.poisoned_docs[doc_id]
        score = sum(body.lower().count(term) for term in query_terms)
        scored.append((score, doc_id, body))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [{"doc_id": d, "score": s, "content": c} for s, d, c in scored[:k] if s > 0]
    if not hits:  # toujours renvoyer quelque chose d'utile
        hits = [{"doc_id": d, "score": 0, "content": c} for _, d, c in scored[:1]]
    return {"query": query, "results": hits}


TOOLS = {"search_docs": search_docs}
