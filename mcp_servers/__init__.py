"""Serveurs MCP (domaines docs, tickets, db, messaging, config, rogue).

Dans ce labo, les outils sont exposes en intra-processus a l'agent via `Toolbox`
(fidelite de mesure identique : chaque appel est journalise dans audit.jsonl).
Un exemple de serveur FastMCP "vrai stdio" est fourni dans `mcp_servers/fastmcp_docs.py`
pour montrer l'interface MCP ; le harness d'eval utilise la Toolbox intra-processus
pour rester reproductible et hors-ligne.
"""
