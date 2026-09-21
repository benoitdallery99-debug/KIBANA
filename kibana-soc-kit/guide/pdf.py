"""Construit les documents imprimables (WeasyPrint), à partir de la MÊME source
que le guide HTML — SPEC §8.

Produit pour l'instant :
- dist/guide.pdf       page de titre, sommaire paginé, signets, en-têtes et
                       pieds courants, exercices SANS leurs solutions, solutions
                       rassemblées en annexe ;
- dist/fiche-memo.pdf  A4 recto verso, lisible en noir et blanc.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import GUIDE, charger_modules, contexte_du_manifeste

from outils import conf

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
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def rendre(nom_gabarit: str, cible: Path, **variables) -> None:
    html = env().get_template(nom_gabarit).render(css_polices=CSS_POLICES, **variables)
    DIST.mkdir(parents=True, exist_ok=True)
    # base_url pointe sur guide/ pour que les chemins de polices se résolvent.
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
