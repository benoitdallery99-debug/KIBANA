"""Lecture de kit.config.yaml — seule source de vérité des paramètres du kit.

Aucun paramètre (version, locale, graine, port…) ne doit être écrit en dur ailleurs :
tout passe par ce module. Voir CLAUDE.md, section « Contraintes non négociables ».
"""

from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any

import yaml

# Racine du kit : le répertoire qui contient kit.config.yaml.
RACINE = Path(__file__).resolve().parent.parent
CHEMIN_CONFIG = RACINE / "kit.config.yaml"

# Ports du lab. Ils ne sont pas dans kit.config.yaml : ce fichier ne décrit que la
# plateforme cible (CLAUDE.md), pas la machine de fabrication. Surchargeables par
# l'environnement pour permettre plusieurs labs sur un même poste.
PORT_ES = int(os.environ.get("KIT_PORT_ES", "9200"))
PORT_KIBANA = int(os.environ.get("KIT_PORT_KIBANA", "5601"))

NOM_POD = os.environ.get("KIT_NOM_POD", "kibana-soc-lab")


@functools.lru_cache(maxsize=1)
def conf() -> dict[str, Any]:
    """Renvoie kit.config.yaml désérialisé, avec les contrôles de cohérence."""
    if not CHEMIN_CONFIG.exists():
        raise SystemExit(f"kit.config.yaml introuvable : {CHEMIN_CONFIG}")
    with CHEMIN_CONFIG.open(encoding="utf-8") as f:
        c = yaml.safe_load(f)

    manquants = [
        chemin
        for chemin in (
            "stack.version",
            "stack.licence",
            "kibana.locale",
            "kibana.vue_solution",
            "formation.space_id",
            "donnees.graine",
            "donnees.fenetre_jours",
            "donnees.fuseau_metier",
            "donnees.namespace",
            "donnees.data_view_id",
            "donnees.data_view_motif",
            "epreuve.graine",
            "epreuve.namespace",
            "epreuve.data_view_id",
            "epreuve.data_view_motif",
        )
        if _lire(c, chemin) is None
    ]
    if manquants:
        raise SystemExit("kit.config.yaml incomplet, clés manquantes : " + ", ".join(manquants))

    if c["stack"]["licence"] != "basic":
        raise SystemExit(
            "stack.licence doit rester « basic » : le parcours n'enseigne que ce qui existe "
            "en licence Basic (CLAUDE.md)."
        )
    if str(_lire(c, "stack.version")).startswith("<<"):
        raise SystemExit("stack.version n'a pas été substituée dans kit.config.yaml.")
    return c


def _lire(c: dict[str, Any], chemin: str) -> Any:
    courant: Any = c
    for partie in chemin.split("."):
        if not isinstance(courant, dict) or partie not in courant:
            return None
        courant = courant[partie]
    return courant


def valeur(chemin: str) -> Any:
    """Lit une clé pointée, ex. valeur("donnees.graine")."""
    v = _lire(conf(), chemin)
    if v is None:
        raise KeyError(f"clé absente de kit.config.yaml : {chemin}")
    return v


def version() -> str:
    return str(valeur("stack.version"))


def majeure() -> int:
    return int(version().split(".")[0])


def mineure() -> int:
    return int(version().split(".")[1])


def au_moins(version_cible: str) -> bool:
    """Vrai si stack.version >= version_cible (comparaison numérique par composant)."""

    def tuple_de(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split("."))

    return tuple_de(version()) >= tuple_de(version_cible)


def url_es() -> str:
    return os.environ.get("KIT_URL_ES", f"http://localhost:{PORT_ES}")


def url_kibana() -> str:
    return os.environ.get("KIT_URL_KIBANA", f"http://localhost:{PORT_KIBANA}")


def secrets() -> dict[str, str]:
    """Lit le .env généré à l'installation. Jamais commité (voir .gitignore)."""
    chemin = RACINE / ".env"
    if not chemin.exists():
        raise SystemExit(
            ".env absent : lancez « make lab-up », qui engendre les mots de passe et les clés."
        )
    valeurs: dict[str, str] = {}
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, val = ligne.partition("=")
        valeurs[cle.strip()] = val.strip()
    return valeurs


def auth_elastic() -> tuple[str, str]:
    return "elastic", secrets()["ELASTIC_PASSWORD"]


# Facteur d'échelle auquel les captures d'écran sont prises. Il vit ICI et non
# dans verif/e2e/kibana.py parce que guide/build.py en a besoin pour écrire le
# CSS : l'y chercher faisait dépendre la construction du guide de Playwright,
# donc d'un navigateur de 150 Mo, sur un poste hors ligne qui ne lance aucun
# test. Mesuré : le guide ne se reconstruisait pas là où il en avait le plus
# besoin. Une seule valeur, deux lecteurs, aucune dépendance de l'un à l'autre.
ECHELLE_DES_CAPTURES = 2
