# MCP Red-Team Lab -- commandes principales.
# Sous Windows sans `make`, lancer directement les commandes `uv run ...` equivalentes
# (voir README, section "Demarrage rapide").

PY ?= uv run
CONFIG ?= none
MODEL ?= mock
REPS ?= 3

.PHONY: help install up data test eval baseline ablation figures dashboard lint typecheck clean

help:
	@echo "Cibles : install | up | data | test | eval | baseline | ablation | figures | dashboard | lint | typecheck | clean"

install:          ## Installer les dependances (dev + llm + dashboard)
	uv sync --all-extras

up: data          ## Preparer l'environnement (donnees fictives + canaries)
	@echo "Environnement pret. Donnees fictives dans data/seed/, canaries dans data/canaries.json"

data:             ## (Re)generer les donnees fictives et les canary tokens
	$(PY) python -m data.generate

test:             ## Tests unitaires
	$(PY) pytest

eval:             ## Lancer un run d'eval. Ex: make eval CONFIG=D1 MODEL=mock REPS=3
	$(PY) python -m eval.run --config $(CONFIG) --model $(MODEL) --reps $(REPS)

baseline:         ## ASR sans defense -> results/baseline.csv
	$(PY) python -m eval.run --config none --model $(MODEL) --reps $(REPS) --out results/baseline.csv

ablation:         ## Ablation complete (toutes les configs) -> results/ablation.csv
	$(PY) python -m eval.run --ablation --model $(MODEL) --reps $(REPS) --out results/ablation.csv

figures:          ## (Re)generer les figures a partir des CSV
	$(PY) python -m eval.analyze

dashboard:        ## Lancer le dashboard Streamlit (mode replay, lit les CSV)
	$(PY) streamlit run dashboard/app.py

lint:
	$(PY) ruff check .

typecheck:
	$(PY) mypy agent mcp_servers defenses eval

clean:            ## Nettoyer les artefacts d'execution
	rm -rf runtime runtime_traces .pytest_cache .ruff_cache .mypy_cache
