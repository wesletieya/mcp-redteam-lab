"""Dashboard Streamlit en mode "replay" : lit uniquement les CSV precalcules.

Aucun appel API, aucune cle exposee, aucun cout -> deployable sur Hugging Face Spaces.
Lancer : streamlit run dashboard/app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "results" / "ablation.csv"

st.set_page_config(page_title="MCP Red-Team Lab", layout="wide")


@st.cache_data
def load(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["attack_success"] = pd.to_numeric(df["attack_success"], errors="coerce")
    return df


st.title("MCP Red-Team Lab -- resultats")
st.caption("Mesure du taux de succes d'attaques (ASR) contre un agent MCP, avant/apres defenses. "
           "Mode replay : donnees precalculees, aucun appel API.")

csv_path = DEFAULT_CSV
if not csv_path.exists():
    st.warning("Aucun resultat trouve. Lancez `make ablation` pour generer results/ablation.csv.")
    st.stop()

df = load(str(csv_path))
atk = df[df["category"] != "legit"]
legit = df[df["category"] == "legit"]

page = st.sidebar.radio("Page", ["Resultats", "Compromis", "Rejouer une attaque"])
models = sorted(df["model"].unique())
model = st.sidebar.selectbox("Modele", models)

atk_m = atk[atk["model"] == model]
legit_m = legit[legit["model"] == model]

if page == "Resultats":
    st.subheader("Heatmap ASR (categorie x configuration)")
    pivot = atk_m.pivot_table(index="category", columns="config",
                              values="attack_success", aggfunc="mean") * 100
    st.dataframe(pivot.style.background_gradient(cmap="Reds", vmin=0, vmax=100).format("{:.0f}"))

    st.subheader("ASR global par configuration")
    asr = (atk_m.groupby("config")["attack_success"].mean() * 100).round(1)
    st.bar_chart(asr)

elif page == "Compromis":
    st.subheader("Securite vs utilite vs cout")
    sec = (1 - atk_m.groupby("config")["attack_success"].mean()) * 100
    util = legit_m.groupby("config")["utility"].mean() * 100
    cost = df[df["model"] == model].groupby("config")["tokens"].mean()
    conf = df[df["model"] == model].groupby("config")["confirmations"].mean()
    table = pd.DataFrame({"securite_%": sec.round(1), "utilite_%": util.round(1),
                          "tokens_moy": cost.round(0), "confirmations_moy": conf.round(2)})
    st.dataframe(table)
    st.scatter_chart(table.reset_index(), x="utilite_%", y="securite_%", size="tokens_moy", color="config")

elif page == "Rejouer une attaque":
    st.subheader("Rejouer un scenario")
    scn = st.selectbox("Scenario", sorted(atk_m["scenario"].unique()))
    cfg = st.selectbox("Configuration", sorted(atk_m["config"].unique()))
    sub = atk_m[(atk_m["scenario"] == scn) & (atk_m["config"] == cfg)]
    if sub.empty:
        st.info("Pas de donnee pour cette combinaison.")
    else:
        r = sub.iloc[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Attaque reussie", "OUI" if r["attack_success"] == 1 else "NON")
        col2.metric("Tokens", int(r["tokens"]))
        col3.metric("Confirmations", int(r["confirmations"]))
        st.write(f"**Categorie** : {r['category']} | **Vecteur** : {r['vector']}")
        st.caption("Pour les traces detaillees pas-a-pas, brancher Langfuse (cf. docs/).")
