"""verif-guide — ce que prouve cette suite (SPEC §10) :

zéro requête externe à l'ouverture ; axe-core injecté sans violation « serious »
ni « critical » ; fichier de 20 Mo au plus ; liens internes valides ; texte
alternatif sur toutes les images ; empreintes conformes au manifeste et AUCUNE
réponse attendue publiée en clair.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from outils.fuites import chercher as chercher_fuites
from verif.e2e import kibana as K

pytestmark = pytest.mark.guide

GRAVITES_REFUSEES = {"serious", "critical"}


@pytest.fixture(scope="module")
def guide(config):
    chemin = config.RACINE / "dist" / "guide.html"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : dist/guide.html absent. Lancez « make guide ».")
    return chemin


@pytest.fixture(scope="module")
def html(guide):
    return guide.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def manifeste(config):
    chemin = config.RACINE / "data" / "manifest.json"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : data/manifest.json absent.")
    return json.loads(chemin.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page_ouverte(guide):
    """Ouvre le guide en file://, comme le fera le stagiaire, et relève tout
    ce que la page tente de charger depuis le réseau."""
    with sync_playwright() as p:
        lanceur = p.chromium.launch(
            executable_path=K.CHROMIUM if Path(K.CHROMIUM).exists() else None,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        contexte = lanceur.new_context(
            locale="fr-FR", timezone_id="Europe/Paris",
            viewport={"width": 1440, "height": 900},
        )
        page = contexte.new_page()
        externes: list[str] = []
        page.on("request", lambda r: (
            externes.append(r.url)
            if not r.url.startswith(("file://", "data:", "blob:")) else None
        ))
        page.goto(f"file://{guide.resolve()}", wait_until="networkidle")
        page.wait_for_timeout(1500)
        yield page, externes
        contexte.close()
        lanceur.close()


# --------------------------------------------------------------------------

def test_aucune_requete_externe(page_ouverte):
    """Le livrable ne télécharge jamais rien (CLAUDE.md, SPEC §3.1)."""
    _, externes = page_ouverte
    assert not externes, f"le guide a tenté {len(externes)} requête(s) : {externes[:5]}"


def test_taille_sous_vingt_mo(guide):
    taille = guide.stat().st_size
    assert taille <= 20 * 1024 * 1024, f"{taille / 1024 / 1024:.1f} Mo, limite 20 Mo"


def test_un_seul_fichier_sans_ressource_locale(html):
    """Tout est inliné : ni CSS, ni JS, ni image en fichier séparé."""
    liens = re.findall(r'<link[^>]+rel=["\']stylesheet["\']', html, re.I)
    assert not liens, f"{len(liens)} feuille(s) de style externe(s)"
    scripts = re.findall(r'<script[^>]+src=', html, re.I)
    assert not scripts, f"{len(scripts)} script(s) externe(s)"
    images = re.findall(r'<img[^>]+src=["\'](?!data:)([^"\']+)', html, re.I)
    assert not images, f"images non inlinées : {images[:5]}"


def test_toutes_les_images_ont_un_texte_alternatif(page_ouverte):
    page, _ = page_ouverte
    sans_alt = page.evaluate("""() =>
        Array.from(document.images)
             .filter(i => !i.getAttribute('alt'))
             .map(i => (i.getAttribute('src')||'').slice(0, 60))
    """)
    assert not sans_alt, f"images sans texte alternatif : {sans_alt}"


def test_liens_internes_valides(page_ouverte):
    page, _ = page_ouverte
    casses = page.evaluate("""() =>
        Array.from(document.querySelectorAll('a[href^="#"]'))
             .map(a => a.getAttribute('href').slice(1))
             .filter(id => id && !document.getElementById(id))
    """)
    assert not casses, f"ancres internes introuvables : {sorted(set(casses))}"


def test_accessibilite_axe_core(page_ouverte, config):
    """axe-core injecté dans la page ouverte, sans violation serious ni critical."""
    page, _ = page_ouverte
    axe = config.RACINE / "verif" / "outils" / "axe.min.js"
    if not axe.exists():
        pytest.skip("NON EXÉCUTÉ : verif/outils/axe.min.js absent.")
    page.add_script_tag(content=axe.read_text(encoding="utf-8"))
    resultat = page.evaluate("""async () => {
        const r = await window.axe.run(document, {
            resultTypes: ['violations'],
            runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }
        });
        return r.violations.map(v => ({
            id: v.id, impact: v.impact, help: v.help,
            noeuds: v.nodes.slice(0, 3).map(n => n.html.slice(0, 120))
        }));
    }""")
    graves = [v for v in resultat if v["impact"] in GRAVITES_REFUSEES]
    assert not graves, (
        "violations d'accessibilité serious ou critical :\n  "
        + "\n  ".join(
            f"[{v['impact']}] {v['id']} — {v['help']} · {v['noeuds']}" for v in graves
        )
    )


def test_empreintes_conformes_au_manifeste(html, manifeste):
    """Les empreintes publiées doivent être exactement celles du manifeste."""
    publiees = set()
    for groupe in re.findall(r'data-empreintes="([^"]*)"', html):
        publiees.update(h for h in groupe.split(",") if h)
    assert publiees, "aucune empreinte publiée : la validation des réponses ne peut pas marcher"

    blocs = [manifeste["reperes"], *manifeste["scenarios"]]
    connues = {h for b in blocs for r in b["reponses"] for h in r["empreintes"]}
    inconnues = publiees - connues
    assert not inconnues, f"{len(inconnues)} empreinte(s) étrangère(s) au manifeste"


def test_aucune_reponse_attendue_publiee(html, manifeste):
    """Le guide n'embarque que des empreintes (SPEC §5.3).

    Les valeurs que la fiche de contexte publie légitimement sont écartées par
    outils/fuites.py, règle partagée avec le constructeur.
    """
    fuites = chercher_fuites(html, manifeste)
    assert not fuites, "réponses attendues publiées en clair :\n  " + "\n  ".join(fuites)


def test_le_manifeste_n_est_pas_embarque(html):
    """Une erreur classique : inliner le manifeste « pour plus tard »."""
    for marque in ('"controle"', '"requete_dsl"', '"valeur":', "aggregations"):
        assert marque not in html, f"le guide contient « {marque} » : le manifeste a fuité"


def test_validation_d_une_reponse_fonctionne(page_ouverte, manifeste):
    """Preuve de bout en bout : une bonne réponse est acceptée, une mauvaise non.

    C'est le cœur du guide : si la validation refusait une réponse juste, le
    stagiaire perdrait confiance dans tout le reste.
    """
    page, _ = page_ouverte
    blocs = [manifeste["reperes"], *manifeste["scenarios"]]
    par_cle = {f"{b['id']}.{r['cle']}": r for b in blocs for r in b["reponses"]}

    cible = page.evaluate("""() => {
        const b = document.querySelector('[data-exercice][data-empreintes]');
        return b ? {id: b.getAttribute('data-exercice'),
                    empreintes: b.getAttribute('data-empreintes')} : null;
    }""")
    if not cible:
        pytest.skip("NON EXÉCUTÉ : aucun exercice à réponse dans le guide")

    attendue = next(
        (r for r in par_cle.values()
         if set(r["empreintes"]) & set(cible["empreintes"].split(","))),
        None,
    )
    assert attendue, f"empreintes de {cible['id']} introuvables dans le manifeste"

    def essayer(valeur: str) -> str:
        page.fill(f'#rep-{cible["id"]}', str(valeur))
        page.click(f'[data-exercice="{cible["id"]}"] [data-verifier]')
        page.wait_for_timeout(700)
        return page.get_attribute(
            f'[data-exercice="{cible["id"]}"] .reponse__retour', "data-etat"
        )

    assert essayer(attendue["valeur"]) == "juste", (
        f"la bonne réponse à {cible['id']} est refusée par le guide"
    )
    assert essayer("valeur manifestement fausse") == "faux", (
        f"une réponse fausse est acceptée par le guide pour {cible['id']}"
    )
