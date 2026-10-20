"""Genere les figures a partir d'un CSV de resultats.

- results/figures/asr_heatmap.png : ASR (categorie x configuration)
- results/figures/tradeoff.png    : securite (1-ASR) x utilite x cout par configuration
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "results" / "figures"


def _load(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV introuvable : {csv_path}. Lancez d'abord `make ablation`.")
    return pd.read_csv(csv_path)


def heatmap(df: pd.DataFrame, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    atk = df[df["category"] != "legit"].copy()
    atk["attack_success"] = pd.to_numeric(atk["attack_success"], errors="coerce")
    pivot = atk.pivot_table(index="category", columns="config", values="attack_success", aggfunc="mean") * 100

    fig, ax = plt.subplots(figsize=(1.2 * len(pivot.columns) + 2, 0.7 * len(pivot.index) + 2))
    im = ax.imshow(pivot.values, cmap="Reds", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        color="white" if v > 50 else "black", fontsize=8)
    ax.set_title("ASR (%) par categorie et configuration")
    fig.colorbar(im, ax=ax, label="ASR %")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"Figure : {out}")


def tradeoff(df: pd.DataFrame, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    atk = df[df["category"] != "legit"].copy()
    atk["attack_success"] = pd.to_numeric(atk["attack_success"], errors="coerce")
    sec = (1 - atk.groupby("config")["attack_success"].mean()) * 100
    util = df[df["category"] == "legit"].groupby("config")["utility"].mean() * 100
    cost = df.groupby("config")["tokens"].mean()

    fig, ax = plt.subplots(figsize=(7, 5))
    for cfg in sec.index:
        if cfg in util.index:
            ax.scatter(util[cfg], sec[cfg], s=40 + cost.get(cfg, 0) / 20, alpha=0.7)
            ax.annotate(cfg, (util[cfg], sec[cfg]), fontsize=8,
                        xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("Utilite (% taches legitimes reussies)")
    ax.set_ylabel("Securite (100 - ASR, %)")
    ax.set_title("Compromis securite / utilite (taille = cout tokens)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"Figure : {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=ROOT / "results" / "ablation.csv")
    args = ap.parse_args()
    df = _load(args.csv)
    heatmap(df, FIG_DIR / "asr_heatmap.png")
    tradeoff(df, FIG_DIR / "tradeoff.png")


if __name__ == "__main__":
    main()
