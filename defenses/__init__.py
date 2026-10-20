"""Defenses en couches (D1 a D6).

Principe : les defenses deterministes (D3 moindre privilege, D4 filtre de sortie, D6 plan
fige) vivent dans le code, jamais dans le prompt. D1 (spotlighting) combine une regle
systeme et un balisage des donnees. D2 est un classifieur. D5 est une validation humaine.
"""
