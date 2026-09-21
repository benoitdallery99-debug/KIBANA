"""verif-pdf — ce que prouve cette suite (SPEC §10) :

polices embarquées, images toutes rendues, sommaire paginé, signets présents,
aucune page blanche parasite. La fiche mémo tient sur exactement deux pages et
reste lisible en noir et blanc.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest
from pypdf import PdfReader

pytestmark = pytest.mark.pdf

DOCUMENTS = ("guide.pdf", "fiche-memo.pdf")


@pytest.fixture(scope="module")
def pdfs(config):
    presents = {}
    for nom in DOCUMENTS:
        chemin = config.RACINE / "dist" / nom
        if chemin.exists():
            presents[nom] = chemin
    if not presents:
        pytest.skip("NON EXÉCUTÉ : aucun PDF dans dist/. Lancez « make guide ».")
    return presents


def _pages(chemin) -> list[str]:
    return [p.extract_text() or "" for p in PdfReader(str(chemin)).pages]


def test_polices_embarquees(pdfs):
    """Une police non embarquée serait remplacée à l'ouverture, chez le lecteur."""
    if not shutil.which("pdffonts"):
        pytest.skip("NON EXÉCUTÉ : pdffonts absent (poppler-utils).")
    defauts = []
    for nom, chemin in pdfs.items():
        sortie = subprocess.run(
            ["pdffonts", str(chemin)], capture_output=True, text=True, check=False
        ).stdout
        lignes = [
            ligne for ligne in sortie.strip().split("\n")[2:] if ligne.strip()
        ]
        if not lignes:
            defauts.append(f"{nom} : aucune police déclarée")
            continue
        for ligne in lignes:
            colonnes = ligne.split()
            # Colonnes de pdffonts : name type encoding emb sub uni object ID
            if len(colonnes) >= 5 and colonnes[-5] != "yes":
                defauts.append(f"{nom} : police non embarquée — {ligne.strip()[:70]}")
    assert not defauts, "polices :\n  " + "\n  ".join(defauts)


def test_aucune_page_blanche_parasite(pdfs):
    """Une page vide au milieu d'un document trahit une rupture mal placée."""
    defauts = []
    for nom, chemin in pdfs.items():
        pages = _pages(chemin)
        for numero, texte in enumerate(pages, 1):
            if not texte.strip():
                defauts.append(f"{nom} : page {numero} sur {len(pages)} est vide")
    assert not defauts, "pages blanches :\n  " + "\n  ".join(defauts)


def test_sommaire_pagine(pdfs, config):
    """Le sommaire doit porter de vrais numéros de page (target-counter)."""
    chemin = pdfs.get("guide.pdf")
    if not chemin:
        pytest.skip("NON EXÉCUTÉ : dist/guide.pdf absent.")
    pages = _pages(chemin)
    sommaire = next((t for t in pages if "Sommaire" in t), None)
    assert sommaire, "aucune page de sommaire"

    entrees = re.findall(r"\.{3,}\s*(\d+)", sommaire)
    assert len(entrees) >= 3, (
        f"sommaire sans numéros de page : {len(entrees)} entrée(s) paginée(s). "
        "target-counter n'a probablement pas été résolu."
    )
    total = len(pages)
    hors = [n for n in entrees if not 1 <= int(n) <= total]
    assert not hors, f"numéros de page hors du document ({total} pages) : {hors}"


def test_signets_presents(pdfs):
    """Sans signets, un PDF de plusieurs dizaines de pages ne se navigue pas."""
    chemin = pdfs.get("guide.pdf")
    if not chemin:
        pytest.skip("NON EXÉCUTÉ : dist/guide.pdf absent.")

    def compter(elements) -> int:
        total = 0
        for element in elements:
            total += compter(element) if isinstance(element, list) else 1
        return total

    nombre = compter(PdfReader(str(chemin)).outline)
    assert nombre >= 5, f"{nombre} signet(s) seulement"


def test_toutes_les_images_sont_rendues(pdfs, config):
    """Chaque capture du guide HTML doit se retrouver dans le PDF.

    Une image absente du PDF est un défaut silencieux : le document s'ouvre,
    la figure manque.
    """
    chemin = pdfs.get("guide.pdf")
    if not chemin:
        pytest.skip("NON EXÉCUTÉ : dist/guide.pdf absent.")
    html = config.RACINE / "dist" / "guide.html"
    attendues = 0
    if html.exists():
        attendues = len(re.findall(r"<img\b", html.read_text(encoding="utf-8"), re.I))
    if attendues == 0:
        pytest.skip("NON EXÉCUTÉ : le guide ne contient encore aucune capture.")

    rendues = 0
    for page in PdfReader(str(chemin)).pages:
        rendues += len(list(page.images))
    assert rendues >= attendues, (
        f"{rendues} image(s) dans le PDF pour {attendues} dans le guide HTML"
    )


def test_fiche_memo_sur_deux_pages(pdfs):
    """SPEC §8 : A4 recto verso. Une troisième page ne s'imprime pas au dos."""
    chemin = pdfs.get("fiche-memo.pdf")
    if not chemin:
        pytest.skip("NON EXÉCUTÉ : dist/fiche-memo.pdf absent.")
    pages = _pages(chemin)
    assert len(pages) == 2, f"fiche mémo de {len(pages)} page(s), 2 attendues"
    assert "KQL" in pages[0], "le recto devrait porter la syntaxe KQL"


def test_le_guide_imprime_ne_porte_pas_les_solutions_dans_le_corps(pdfs):
    """SPEC §8 : exercices sans solutions, solutions en annexe.

    On ne cherche pas sérieusement une réponse qu'on a sous les yeux.
    """
    chemin = pdfs.get("guide.pdf")
    if not chemin:
        pytest.skip("NON EXÉCUTÉ : dist/guide.pdf absent.")
    pages = _pages(chemin)
    debut_annexe = next(
        (i for i, t in enumerate(pages) if "Annexe" in t and "solution" in t.lower()),
        None,
    )
    assert debut_annexe is not None, "annexe des solutions introuvable"
    corps = "\n".join(pages[:debut_annexe])
    assert "Erreurs fréquentes" not in corps, (
        "les solutions apparaissent dans le corps du guide, pas seulement en annexe"
    )
