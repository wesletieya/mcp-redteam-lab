"""DefenseConfig : un drapeau par defense, pour mesurer chaque couche seule ou combinee."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DefenseConfig:
    d1_spotlighting: bool = False     # Delimiter + marquer les sorties d'outil comme donnees
    d2_input_filter: bool = False     # Classifieur d'injection sur chaque sortie d'outil
    d3_least_privilege: bool = False  # Outils exposes selon la tache, DB lecture seule, allowlists
    d4_output_filter: bool = False    # Detection canaries/PII dans les arguments d'outils sortants
    d5_hitl: bool = False             # Confirmation humaine avant action sensible
    d6_planner: bool = False          # Plan fige : l'executeur ne peut pas ajouter d'appel

    # Profil d'humain simule pour D5 : "attentive" (n'approuve que le lie a la tache) ou "tired" (tout).
    human_profile: str = "attentive"

    def label(self) -> str:
        on = [n for n, v in self.flags().items() if v]
        return "none" if not on else "+".join(on)

    def flags(self) -> dict[str, bool]:
        return {k.upper().split("_")[0]: v for k, v in asdict(self).items()
                if k.startswith("d") and isinstance(v, bool)}

    @classmethod
    def from_label(cls, label: str, human_profile: str = "attentive") -> DefenseConfig:
        """Construit depuis un label type 'none', 'D1', 'D3+D4', 'all', 'all+D6'."""
        mapping = {
            "D1": "d1_spotlighting", "D2": "d2_input_filter", "D3": "d3_least_privilege",
            "D4": "d4_output_filter", "D5": "d5_hitl", "D6": "d6_planner",
        }
        kwargs: dict[str, bool] = {}
        if label in ("all", "all+D6", "toutes"):
            kwargs = {v: True for v in mapping.values()}
            if label == "all+D6":
                kwargs["d6_planner"] = True
        elif label != "none":
            for part in label.split("+"):
                part = part.strip()
                if part in mapping:
                    kwargs[mapping[part]] = True
        return cls(human_profile=human_profile, **kwargs)


# Configurations de l'ablation (environ 10, cf. plan semaine 4).
ABLATION_LABELS = [
    "none", "D1", "D2", "D3", "D4", "D5", "D6",
    "D1+D2", "D3+D4", "all", "all+D6",
]
