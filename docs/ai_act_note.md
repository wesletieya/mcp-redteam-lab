# Note AI Act — MCP Red-Team Lab

> **Ce document est une démarche d'ingénierie, pas un avis juridique.** Il met en regard les
> contrôles techniques du projet et les exigences de l'AI Act de l'UE, à titre pédagogique.
> Vérifier le statut d'adoption définitive et le calendrier le jour de la publication.

## 1. Description du système et classification de risque

Le système est un **assistant d'exploitation** (agent LLM + outils MCP) pour une
constellation satellite fictive, en bac à sable. Dans un déploiement réel, un tel assistant
**ne serait probablement pas « à haut risque »** au sens de l'annexe III : il assiste des
opérateurs qualifiés sans prendre de décision autonome à effet juridique ou de sécurité
critique.

Il **le deviendrait** si :
- il pilotait directement une fonction de sécurité (commande réelle d'un actif spatial,
  sans supervision humaine effective) — proximité avec les « infrastructures critiques »
  (annexe III §2) ;
- il était intégré comme composant de sécurité d'un produit déjà régulé.

Dans ce cas, les exigences des articles 9 à 15 (gestion des risques, données, documentation,
journalisation, supervision humaine, robustesse) s'appliqueraient.

## 2. Correspondance contrôles ↔ articles

| Exigence AI Act | Article | Contrôle dans ce projet |
|---|---|---|
| Journalisation / traçabilité | art. 12 | `audit.jsonl` + `outbox.jsonl` (chaque appel d'outil tracé) ; tracing Langfuse optionnel |
| Supervision humaine | art. 14 | **D5** (confirmation humaine avant action sensible) ; évaluation avec humain « attentif » vs « fatigué » |
| Robustesse & cybersécurité | art. 15 | **D1–D6** + suite d'évaluation (ASR statique **et** adaptatif), CI sécurité |
| Gestion des risques | art. 9 | [threat model](threat_model.md) : actifs, attaquant, catégories OWASP |
| Transparence | art. 50 | documentation publique du système, des limites et de l'éthique |
| Exactitude / résilience | art. 15 | checks déterministes (canaries), répétitions, mesure de l'utilité en regard de l'ASR |

## 3. Calendrier (à revérifier à la publication)

Selon l'accord politique provisoire sur le **Digital Omnibus**, les obligations « haut
risque » de l'**annexe III** seraient repoussées au **2 décembre 2027**, et celles de
l'**annexe I** au **2 août 2028** (source : analyse Gibson Dunn). Ces dates dépendent de
l'adoption définitive du texte — **à vérifier le jour de la publication**.

## 4. Références

- OWASP Top 10 for LLM Applications (2025).
- Recommandations de l'ANSSI sur la sécurité des systèmes d'IA générative.
- CaMeL (Google DeepMind, 2025) ; « Design Patterns for Securing LLM Agents against Prompt
  Injections » (2025).
- AgentDojo (NeurIPS 2024) — méthode d'évaluation reprise ici.

---

*Rappel : rien dans ce document ne constitue un conseil juridique. Pour une mise en
conformité réelle, consulter un juriste spécialisé.*
