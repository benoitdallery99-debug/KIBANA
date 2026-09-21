"""Typographie française appliquée au HTML rendu — CLAUDE.md.

La règle française veut une espace insécable avant les ponctuations hautes
(: ; ! ?) et à l'intérieur des guillemets. Sans elle, le navigateur rejette
la ponctuation ou le guillemet fermant en début de ligne, ce qui se voit
immédiatement sur écran étroit.

Le traitement s'applique au HTML RENDU, et saute soigneusement :
- l'intérieur des balises (une insécable dans un attribut casserait le
  document) ;
- les éléments <pre>, <code>, <script>, <style> — y insérer une insécable
  casserait une requête KQL, ce qui serait bien pire que le défaut corrigé.
"""

from __future__ import annotations

import re

INSECABLE = " "       # avant « : », et dans les guillemets
FINE_INSECABLE = " "  # avant « ; ! ? », usage typographique courant

# Éléments dont le contenu ne doit jamais être touché.
INTOUCHABLES = ("pre", "code", "script", "style", "textarea")

_OUVRANT = re.compile(r"<\s*(" + "|".join(INTOUCHABLES) + r")\b", re.I)
_FERMANT = re.compile(r"<\s*/\s*(" + "|".join(INTOUCHABLES) + r")\s*>", re.I)


def corriger_texte(texte: str) -> str:
    """Applique les espaces insécables à un fragment de TEXTE (pas de balises)."""
    # Une espace ordinaire (ou aucune) devant une ponctuation haute.
    texte = re.sub(r"[ \t]+:", INSECABLE + ":", texte)
    # PIÈGE : le « ; » qui ferme une entité HTML n'est PAS une ponctuation.
    # Sans la garde ci-dessous, « l&#39;écran » devenait « l&#39<espace fine>; »
    # — 1132 fois dans le guide, jusque dans le sommaire et les titres
    # d'exercices, où le lecteur voyait « Pourquoi l' ;écran est-il vide ».
    # La règle typographique reste juste ; c'est son domaine qui était trop
    # large. On ne touche donc pas à un « ; » précédé d'un nom d'entité.
    texte = re.sub(
        r"(?<!&)(?<!&[a-zA-Z0-9#])(?<!&[a-zA-Z0-9#][a-zA-Z0-9])"
        r"(?<!&[a-zA-Z0-9#][a-zA-Z0-9]{2})(?<!&[a-zA-Z0-9#][a-zA-Z0-9]{3})"
        r"(?<!&[a-zA-Z0-9#][a-zA-Z0-9]{4})(?<!&[a-zA-Z0-9#][a-zA-Z0-9]{5})"
        r"[ \t]*([;!?])",
        FINE_INSECABLE + r"\1",
        texte,
    )
    # Guillemets français : insécable à l'intérieur.
    texte = re.sub(r"«[ \t]*", "«" + INSECABLE, texte)
    texte = re.sub(r"[ \t]*»", INSECABLE + "»", texte)
    return texte


def corriger_html(html: str) -> str:
    """Applique la typographie aux seuls nœuds de texte du HTML."""
    sortie: list[str] = []
    position = 0
    profondeur_intouchable = 0

    for balise in re.finditer(r"<[^>]*>", html):
        texte = html[position:balise.start()]
        if texte:
            sortie.append(texte if profondeur_intouchable else corriger_texte(texte))
        marque = balise.group(0)
        sortie.append(marque)
        position = balise.end()

        if _OUVRANT.match(marque) and not marque.rstrip().endswith("/>"):
            profondeur_intouchable += 1
        elif _FERMANT.match(marque) and profondeur_intouchable:
            profondeur_intouchable -= 1

    reste = html[position:]
    if reste:
        sortie.append(reste if profondeur_intouchable else corriger_texte(reste))
    return "".join(sortie)


def defauts(texte: str) -> list[str]:
    """Signale les ponctuations hautes précédées d'une espace ORDINAIRE.

    Sert aux vérifications : c'est exactement ce que la règle interdit.
    """
    trouves = []
    for motif, libelle in (
        (r"[a-zA-Zé0-9»] :", "espace ordinaire avant « : »"),
        (r"[a-zA-Zé0-9»] [;!?]", "espace ordinaire avant « ; ! ? »"),
        (r"« [A-Za-zÀ-ÿ0-9]", "espace ordinaire après « « »"),
        (r"[A-Za-zÀ-ÿ0-9.] »", "espace ordinaire avant « » »"),
    ):
        for m in re.finditer(motif, texte):
            trouves.append(f"{libelle} : …{texte[max(0, m.start() - 30):m.end() + 10]}…")
    return trouves


def texte_verifiable(html: str) -> str:
    """Texte du document, hors balises et hors éléments intouchables.

    C'est sur lui que porte le contrôle typographique : le code n'a pas à
    suivre la typographie française, et les attributs ne sont pas du texte.
    """
    morceaux: list[str] = []
    position = 0
    profondeur_intouchable = 0

    for balise in re.finditer(r"<[^>]*>", html):
        if not profondeur_intouchable:
            morceaux.append(html[position:balise.start()])
        marque = balise.group(0)
        position = balise.end()
        if _OUVRANT.match(marque) and not marque.rstrip().endswith("/>"):
            profondeur_intouchable += 1
        elif _FERMANT.match(marque) and profondeur_intouchable:
            profondeur_intouchable -= 1
    if not profondeur_intouchable:
        morceaux.append(html[position:])
    # Attention : str.split() considère U+00A0 comme une espace et le
    # DÉTRUIRAIT — le contrôle signalerait alors des défauts sur du texte
    # pourtant corrigé. On ne normalise donc que les blancs ordinaires.
    return re.sub(r"[ \t\r\n]+", " ", "".join(morceaux)).strip()
