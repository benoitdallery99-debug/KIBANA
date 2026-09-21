"""verif-guide — ce que prouve cette suite (SPEC §10) :

zéro requête externe à l'ouverture ; axe-core injecté sans violation « serious »
ni « critical » ; fichier de 20 Mo au plus ; liens internes valides ; texte
alternatif sur toutes les images ; empreintes conformes au manifeste et AUCUNE
réponse attendue publiée en clair.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from outils.fuites import chercher as chercher_fuites
from outils.typographie import defauts as defauts_typo
from outils.typographie import texte_verifiable
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
    """Une erreur classique : inliner le manifeste « pour plus tard ».

    Le contrôle porte sur des DONNÉES embarquées, pas sur des liens. Les
    valeurs d'attributs href et src sont donc retirées avant l'examen : sans
    cela, une URL de documentation parfaitement légitime — celle de
    l'agrégation cardinality, qui contient le mot « aggregations » — ferait
    échouer le contrôle. Le marqueur est en outre exigé sous sa forme JSON,
    entre guillemets, qui ne peut venir que d'un objet sérialisé.
    """
    sans_liens = re.sub(r'(?:href|src)\s*=\s*"[^"]*"', "", html)
    for marque in ('"controle"', '"requete_dsl"', '"valeur":', '"aggregations"',
                   '"empreintes":', '"scenarios":'):
        assert marque not in sans_liens, (
            f"le guide contient « {marque} » : le manifeste a fuité"
        )


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


def test_typographie_francaise(html):
    """CLAUDE.md : typographie française, espaces insécables comprises.

    Sans elles, le navigateur rejette la ponctuation haute et le guillemet
    fermant en début de ligne — visible dès qu'on lit sur un écran étroit.
    Le contrôle porte sur le texte seul : le code n'a pas à suivre cette
    règle, et une insécable dans une requête KQL la casserait.
    """
    texte = texte_verifiable(html)
    manquantes = defauts_typo(texte)
    assert not manquantes, (
        f"{len(manquantes)} espace(s) insécable(s) manquante(s) :\n  "
        + "\n  ".join(manquantes[:12])
    )
    assert html.count("\u00a0") > 50, (
        "quasiment aucune espace insécable dans le guide : la passe "
        "typographique n'a pas été appliquée"
    )


def test_aucun_debordement_horizontal_sur_telephone(page_ouverte):
    """Le guide se lit sur un téléphone sans faire défiler la page de côté.

    Deux constats distincts, et il faut les deux : la PAGE ne doit jamais
    déborder horizontalement, et aucun bloc de code ne doit être COUPÉ — il doit
    défiler dans son propre cadre. Le défaut trouvé en P8 donnait les deux à la
    fois : « .contenu » est une cellule de grille, donc « min-width: auto », donc
    elle refusait de rétrécir ; « body » masquait le débordement ; la fin des
    requêtes disparaissait. Mesuré, ici, aux deux largeurs de téléphone usuelles.
    """
    page, _ = page_ouverte
    defauts = []
    for largeur in (390, 320):
        page.set_viewport_size({"width": largeur, "height": 800})
        page.wait_for_timeout(600)
        debord = page.evaluate(
            "() => document.documentElement.scrollWidth"
            "     - document.documentElement.clientWidth"
        )
        if debord > 0:
            defauts.append(f"{largeur} px : la page déborde de {debord} px")
        coupes = page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('pre').forEach(p => {
              const ox = getComputedStyle(p).overflowX;
              const defile = ox === 'auto' || ox === 'scroll';
              if (p.scrollWidth > p.clientWidth + 1 && !defile)
                out.push((p.id || p.textContent.slice(0, 40)));
            });
            return out;
        }""")
        if coupes:
            defauts.append(f"{largeur} px : {len(coupes)} bloc(s) de code coupés — {coupes[:3]}")
    page.set_viewport_size({"width": 1440, "height": 900})
    assert not defauts, "mise en page téléphone :\n  " + "\n  ".join(defauts)


def test_lien_d_evitement_present_et_premier(page_ouverte):
    """Un lien d'évitement, et il doit être le PREMIER élément focalisable.

    Le sommaire compte une cinquantaine de liens : sans ce lien, un utilisateur
    au clavier les traverse tous avant d'atteindre le contenu.
    """
    page, _ = page_ouverte
    premier = page.evaluate("""() => {
        const sel = 'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
        for (const el of document.querySelectorAll(sel)) {
          const st = getComputedStyle(el);
          if (st.display === 'none' || st.visibility === 'hidden') continue;
          return {balise: el.tagName, classe: el.className, href: el.getAttribute('href')};
        }
        return null;
    }""")
    assert premier, "aucun élément focalisable trouvé"
    assert "evitement" in (premier["classe"] or ""), (
        f"le premier élément focalisable est {premier} — le lien d'évitement "
        "doit venir en tête"
    )
    cible = (premier["href"] or "").lstrip("#")
    assert cible and page.query_selector(f"#{cible}"), (
        f"le lien d'évitement pointe sur « {premier['href']} », qui n'existe pas"
    )
