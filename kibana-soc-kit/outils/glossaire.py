"""Relie les termes du glossaire à leur définition, en infobulle (SPEC §7.1).

Le guide portait bien un glossaire, mais en liste plate à la fin du document :
un stagiaire qui butait sur « cardinality » au module M2 devait savoir qu'il
existait, le chercher, puis revenir. SPEC §7.1 demande des « infobulles
accessibles », ce qui est autre chose.

Ce module ne marque que la PREMIÈRE occurrence de chaque terme, et seulement
dans du texte courant : jamais dans un bloc de code, un titre, ni à l'intérieur
d'un lien — un terme surligné partout deviendrait un papier peint, et une
infobulle dans un titre casserait la navigation.

Accessibilité : le terme est un « button », donc atteignable au clavier ;
l'infobulle porte « role="tooltip" » et lui est reliée par « aria-describedby »,
de sorte qu'un lecteur d'écran la lit avec le terme. Elle s'affiche au survol ET
à la prise de focus, et se referme par Échap (WCAG 2.1 §1.4.13).
"""

from __future__ import annotations

import html as _html
import re
import unicodedata

# Mêmes éléments intouchables que la typographie, plus les titres et les liens :
# on ne pose pas de bouton dans un « h2 » ni dans un « a ».
INTOUCHABLES = (
    "pre", "code", "script", "style", "textarea",
    "h1", "h2", "h3", "h4", "h5", "h6", "a", "button",
)

_OUVRANT = re.compile(r"<\s*(" + "|".join(INTOUCHABLES) + r")\b", re.I)
_FERMANT = re.compile(r"<\s*/\s*(" + "|".join(INTOUCHABLES) + r")\s*>", re.I)


def ancre(terme: str) -> str:
    """Identifiant stable et sans accent pour un terme."""
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", terme)
        if unicodedata.category(c) != "Mn"
    )
    return "gloss-" + re.sub(r"[^a-z0-9]+", "-", sans_accent.lower()).strip("-")


def _marquage(terme: str, definition: str, vu: str) -> str:
    identifiant = ancre(terme)
    return (
        '<span class="glossaire-lien">'
        f'<button type="button" class="glossaire-lien__terme" '
        f'aria-describedby="{identifiant}">{_html.escape(vu)}</button>'
        f'<span role="tooltip" id="{identifiant}" class="glossaire-lien__bulle">'
        f'{_html.escape(definition)}</span>'
        "</span>"
    )


def lier(html: str, glossaire: list[dict], deja: set[str] | None = None) -> str:
    """Marque la première occurrence de chaque terme dans du texte courant.

    Les termes sont traités du plus long au plus court : sans cela,
    « data view » serait coupé en deux par « data stream » et réciproquement.

    « deja » porte les termes déjà marqués ailleurs, et il est MODIFIÉ au
    passage. Sans lui, chaque appel repart de zéro : appelé une fois par module,
    « KQL » se retrouvait marqué cinq fois dans le même document — cinq bulles
    identiques pour le lecteur, et surtout cinq éléments partageant le même
    « id », ce qu'aucune page valide ne fait et qu'axe-core refuse.
    """
    definitions = {
        t["terme"]: t.get("definition", "")
        for t in glossaire if t.get("terme")
    }
    if deja is None:
        deja = set()
    restants = [
        t for t in sorted(definitions, key=len, reverse=True) if t not in deja
    ]

    sortie: list[str] = []
    position = 0
    profondeur = 0

    def traiter(texte: str) -> str:
        for terme in list(restants):
            motif = re.compile(rf"(?<![\w-]){re.escape(terme)}(?![\w-])", re.I)
            trouve = motif.search(texte)
            if not trouve:
                continue
            restants.remove(terme)
            deja.add(terme)
            return (
                texte[:trouve.start()]
                + _marquage(terme, definitions[terme], trouve.group(0))
                + traiter(texte[trouve.end():])
            )
        return texte

    for balise in re.finditer(r"<[^>]*>", html):
        fragment = html[position:balise.start()]
        if fragment:
            sortie.append(fragment if profondeur else traiter(fragment))
        marque = balise.group(0)
        sortie.append(marque)
        position = balise.end()
        if _OUVRANT.match(marque) and not marque.rstrip().endswith("/>"):
            profondeur += 1
        elif _FERMANT.match(marque) and profondeur:
            profondeur -= 1

    reste = html[position:]
    if reste:
        sortie.append(reste if profondeur else traiter(reste))
    return "".join(sortie)
