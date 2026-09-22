"""Libellés d'interface : la source est Kibana, jamais la mémoire du rédacteur.

CLAUDE.md l'exige : « Libellés d'UI cités : ceux de kibana.locale, relevés dans
le lab, jamais traduits de tête. » Ce module donne de quoi le VÉRIFIER, parce
qu'une règle qu'on ne contrôle pas finit toujours par être enfreinte — elle
l'avait d'ailleurs été (« Métrique » pour « Indicateur », « Heatmap » pour
« Carte thermique », « Secteurs » pour « Camembert »).

Kibana sert son propre catalogue de traductions sur /translations/<locale>.json,
sans authentification. C'est le même fichier que celui embarqué dans l'image,
donc la référence exacte de la version du lab.

Certains libellés N'Y SONT PAS et c'est normal : quelques entrées de navigation
restent en anglais en 9.5.3, même en fr-FR. Elles sont listées nommément dans
ANGLAIS_ASSUME, avec ce qu'elles désignent — les citer en français enverrait le
stagiaire chercher un intitulé qui n'existe pas à l'écran.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import requests

from outils import conf

# Libellés que Kibana 9.5.3 laisse en anglais dans la vue de solution « classic »,
# relevés dans le lab le 21/09/2026 (panneau de navigation, Space « formation »).
# Le href constaté est donné : c'est lui qui distingue « Dashboards » (Analytics)
# de « Tableaux de bord », qui est l'entrée de la solution Security.
ANGLAIS_ASSUME = {
    "Dashboards": "/app/dashboards — entrée « Analytics » du panneau de navigation ; "
                  "« Tableaux de bord », qui EST traduit, désigne "
                  "/app/security/dashboards, une autre application",
    "Visualize library": "/app/visualize — entrée « Analytics » ; c'est par là qu'on "
                         "atteint Lens, qui n'a pas d'entrée à lui. Le titre de la "
                         "page, lui, est traduit : « Bibliothèque Visualize »",
    "Analytics": "en-tête de section du panneau de navigation",
    "Language: KQL": "entrée du menu de la barre de requête, celle qui ouvre le "
                     "panneau « Filtrer la langue »",
    "Filter your data using KQL syntax": "texte gris de la barre de requête de "
                     "Discover et des tableaux de bord. Relevé dans le lab : la "
                     "chaîne n'a AUCUNE traduction dans les 60 705 libellés de "
                     "fr-FR. C'est la phrase anglaise la plus vue du parcours — "
                     "elle est à l'écran en permanence, et dans cinq captures "
                     "sur huit",
}

# « Discover », « Maps » et « Machine Learning » NE sont PAS ici : ces trois-là
# figurent bien dans le catalogue, à l'identique — leur nom est le même dans les
# deux langues. Les inscrire en exception les soustrairait au contrôle pour rien.


_CACHE: dict[str, set[str]] | None = None


def normaliser(texte: str) -> str:
    """Forme comparable : accents composés, espaces insécables ramenées, casse.

    Kibana emploie l'espace insécable (U+00A0) dans ses propres libellés
    (« Dernières 15 minutes », « Axe Y »). Comparer sans la neutraliser fait
    échouer des libellés pourtant exacts.
    """
    texte = unicodedata.normalize("NFC", texte)
    texte = texte.replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", texte).strip().lower()


def catalogue(source: str | Path | None = None) -> set[str]:
    """Ensemble des libellés traduits, sous forme normalisée.

    Lit le lab par défaut. « source » permet de passer un fichier déjà extrait,
    pour un contrôle hors ligne.
    """
    global _CACHE
    cle = str(source or "lab")
    if _CACHE is not None and cle in _CACHE:
        return _CACHE[cle]

    if source is not None:
        brut = json.loads(Path(source).read_text(encoding="utf-8"))
    else:
        locale = str(conf.valeur("kibana.locale"))
        r = requests.get(f"{conf.url_kibana()}/translations/{locale}.json", timeout=60)
        r.raise_for_status()
        brut = r.json()

    connus: set[str] = set()
    for valeur in brut.get("messages", {}).values():
        # Le catalogue mêle deux formes : la chaîne nue, et l'objet
        # {"text": ..., "comment": ...} quand le traducteur a laissé une note.
        texte = valeur.get("text") if isinstance(valeur, dict) else valeur
        if isinstance(texte, str) and texte:
            connus.add(normaliser(texte))

    _CACHE = _CACHE or {}
    _CACHE[cle] = connus
    return connus


def inconnus(libelles: list[str], source: str | Path | None = None) -> list[str]:
    """Libellés qui ne figurent NI dans le catalogue, NI dans ANGLAIS_ASSUME."""
    connus = catalogue(source)
    assumes = {normaliser(x) for x in ANGLAIS_ASSUME}
    return [x for x in libelles if normaliser(x) not in connus and normaliser(x) not in assumes]
