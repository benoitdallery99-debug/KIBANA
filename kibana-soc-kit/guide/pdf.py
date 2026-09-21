"""Construit les documents imprimables (WeasyPrint), à partir de la MÊME source
que le guide HTML — SPEC §8.

Produit :
- dist/guide.pdf             page de titre, sommaire paginé, signets, en-têtes
                             et pieds courants, exercices SANS leurs solutions,
                             solutions rassemblées en annexe ;
- dist/fiche-memo.pdf        A4 recto verso, lisible en noir et blanc ;
- dist/guide-formateur.pdf   déroulé minuté, matrice, corrigé, grilles ;
- dist/corriges.pdf          démarches et requêtes, sans les valeurs attendues ;
- dist/quiz-imprimable.pdf   quiz sans réponses, à distribuer ;
- dist/note-de-conception.pdf et dist/rapport-recette.pdf.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import GUIDE, charger_modules, charger_quiz, contexte_du_manifeste

from outils import conf
from outils.typographie import corriger_html

DIST = conf.RACINE / "dist"

# Les polices sont chargées depuis le disque : WeasyPrint les embarque ensuite
# dans le PDF. Elles restent celles distribuées par le projet, non modifiées.
CSS_POLICES = """
@font-face { font-family: "Atkinson Hyperlegible Next";
  src: url("polices/AtkinsonHyperlegibleNext[wght].ttf"); font-weight: 200 800; }
@font-face { font-family: "Atkinson Hyperlegible Next";
  src: url("polices/AtkinsonHyperlegibleNext-Italic[wght].ttf");
  font-weight: 200 800; font-style: italic; }
@font-face { font-family: "Atkinson Hyperlegible Mono";
  src: url("polices/AtkinsonHyperlegibleMono[wght].ttf"); font-weight: 200 800; }
"""


def env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(GUIDE / "gabarits")),
        # PIÈGE : select_autoescape(["html"]) compare la DERNIÈRE extension du
        # fichier. Nos gabarits s'appellent « guide.html.j2 » : leur extension
        # est « .j2 », l'échappement restait donc désactivé partout, et tout
        # « & », « < » ou guillemet venant du parcours partait tel quel dans la
        # page. On l'active sans condition — tous les gabarits sont du HTML — et
        # le seul fragment volontairement injecté, « corps_html », est marqué
        # « | safe » dans les gabarits.
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def rendre(nom_gabarit: str, cible: Path, **variables) -> None:
    html = corriger_html(
        env().get_template(nom_gabarit).render(css_polices=CSS_POLICES, **variables)
    )
    DIST.mkdir(parents=True, exist_ok=True)
    # base_url pointe sur guide/ pour que les chemins de polices se résolvent.
    HTML(string=html, base_url=str(GUIDE) + "/").write_pdf(str(cible))
    print(f"  {cible.relative_to(conf.RACINE)} — {cible.stat().st_size / 1024:.0f} Ko")


DOCUMENT_SIMPLE = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>{titre}</title><style>{polices}</style><style>{css}</style>
<style>h1{{break-before:auto}} h2{{break-before:auto}}</style></head>
<body>{corps}</body></html>"""


def rendre_markdown(source: Path, cible: Path, titre: str) -> None:
    """Rend un document Markdown du dépôt en PDF, avec la même typographie.

    Sert aux documents qui n'ont pas d'exercices : note de conception, guide
    formateur, rapport de recette.
    """
    import markdown as md

    corps = md.markdown(
        source.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    html = corriger_html(DOCUMENT_SIMPLE.format(
        titre=titre,
        polices=CSS_POLICES,
        css=(GUIDE / "styles" / "pdf.css").read_text(encoding="utf-8"),
        corps=corps,
    ))
    DIST.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(GUIDE) + "/").write_pdf(str(cible))
    print(f"  {cible.relative_to(conf.RACINE)} — {cible.stat().st_size / 1024:.0f} Ko")


def main() -> int:
    manifeste, modules, glossaire = charger_modules()
    commun = {
        "version": conf.version(),
        "licence": str(conf.valeur("stack.licence")).capitalize(),
        "locale": str(conf.valeur("kibana.locale")),
        "avertissement_donnees": manifeste["avertissement"],
    }

    rendre(
        "guide-pdf.html.j2",
        DIST / "guide.pdf",
        css=(GUIDE / "styles" / "pdf.css").read_text(encoding="utf-8"),
        titre="Kibana pour analystes SOC",
        sous_titre=(
            "Parcours pratique : chercher, visualiser, et rendre le résultat "
            "durable sous forme de tableau de bord."
        ),
        contexte=contexte_du_manifeste(manifeste),
        modules=modules,
        glossaire=glossaire,
        duree_totale=sum(m["duree_minutes"] for m in modules),
        nb_exercices=sum(len(m["exercices"]) for m in modules),
        **commun,
    )

    # Documents Markdown du dépôt qui ont une version imprimable (SPEC §8).
    for nom_source, nom_cible, titre in (
        ("NOTE_DE_CONCEPTION.md", "note-de-conception.pdf", "Note de conception"),
        ("guide-formateur.md", "guide-formateur.pdf", "Guide du formateur"),
        ("RAPPORT_RECETTE.md", "rapport-recette.pdf", "Rapport de recette"),
    ):
        source = conf.RACINE / "docs" / nom_source
        if not source.exists():
            source = conf.RACINE / "formateur" / nom_source
        if source.exists():
            rendre_markdown(source, DIST / nom_cible, titre)

    # Corrigés : mêmes modules, mais on ne garde que la démarche et les
    # requêtes. Les valeurs attendues n'y figurent pas — elles vivent dans le
    # manifeste, qui reste sur le poste du formateur.
    rendre(
        "corriges.html.j2",
        DIST / "corriges.pdf",
        css=(GUIDE / "styles" / "pdf.css").read_text(encoding="utf-8"),
        titre="Corrigés du parcours",
        modules=modules,
        nb_exercices=sum(len(m["exercices"]) for m in modules),
        **commun,
    )

    quiz = charger_quiz()
    if quiz:
        rendre("quiz-imprimable.html.j2", DIST / "quiz-imprimable.pdf",
               quiz=quiz, **commun)

    memo = yaml.safe_load((GUIDE / "fiche-memo.yaml").read_text(encoding="utf-8"))
    rendre(
        "fiche-memo.html.j2",
        DIST / "fiche-memo.pdf",
        recto=memo["recto"],
        verso=memo["verso"],
        **commun,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
