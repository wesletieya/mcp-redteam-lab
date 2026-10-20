# DEVLOG

Journal court : décisions, surprises, idées pour le post LinkedIn et les entretiens.

## 2026-10-20 — Socle initial

- **Décision : un provider `mock` déterministe en plus des modèles réels.** L'agent `mock`
  est *injectable par construction* (il suit les directives cachées non neutralisées). Ça
  rend le labo rejouable hors-ligne, teste la *logique des défenses* en CI sans clé API, et
  donne une baseline nette (ASR 100 %). Les modèles réels (`anthropic`, `ollama`) branchent
  la même interface `run_episode(task, toolbox)` pour les mesures réalistes.
- **Surprise utile : aucune défense seule ne descend sous 12,5 % d'ASR.** Et D3+D4, le
  réflexe « moindre privilège + filtre de sortie », reste à 12,5 % à cause de la
  manipulation de *contenu* (faire recommander une mauvaise procédure), qu'aucune de ces
  deux couches ne voit. → argument fort pour la défense en couches.
- **Le point qui fait mouche en entretien : l'attaque adaptative inverse le classement.**
  En statique, D1/D2 (spotlighting/classifieur) paraissent excellentes ; une charge encodée
  en base64 les contourne toutes les deux, mais D3/D4/D5/D6 la bloquent. Complémentarité
  prompt-level ↔ système.
- **À faire ensuite :** passer de 8→~60 attaques et 7→~30 tâches ; brancher un vrai modèle
  et mesurer la variabilité (3 reps, IC) ; attaques adaptatives supplémentaires (paraphrase,
  découpage multi-messages, canary encodé vs D4) ; déployer le dashboard sur HF Spaces ;
  tourner la vidéo de 2 min.

## Idées d'accroche LinkedIn
- « J'ai attaqué mon propre agent IA 264 fois. Sans défense : 100 % des attaques passent.
  Avec une défense en couches : 0 %. Mais chaque défense prise seule laisse un trou. »
