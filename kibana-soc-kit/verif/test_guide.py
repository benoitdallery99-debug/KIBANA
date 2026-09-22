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
import yaml
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


# Largeurs auditées. La passe était figée à 1 440 px, et c'est précisément
# SOUS 992 px que la mise en page bascule : les tableaux y deviennent des zones
# défilantes, et la violation « serious » qu'ils portaient ne pouvait pas être
# vue. SPEC §7.3 exige le téléphone ; on l'audite donc, aux deux largeurs qui
# comptent — l'iPhone SE et le format le plus répandu.
LARGEURS_AUDITEES = (1440, 375, 320)


def _violations_axe(page, axe_js: str) -> list[dict]:
    page.add_script_tag(content=axe_js)
    return page.evaluate("""async () => {
        const r = await window.axe.run(document, {
            resultTypes: ['violations'],
            runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }
        });
        return r.violations.map(v => ({
            id: v.id, impact: v.impact, help: v.help,
            noeuds: v.nodes.slice(0, 3).map(n => n.html.slice(0, 120))
        }));
    }""")


def test_accessibilite_axe_core(page_ouverte, config):
    """axe-core injecté dans la page ouverte, sans violation serious ni critical.

    À trois largeurs, parce qu'une mise en page qui bascule change ses
    violations en même temps que sa forme.
    """
    page, _ = page_ouverte
    axe = config.RACINE / "verif" / "outils" / "axe.min.js"
    if not axe.exists():
        pytest.skip("NON EXÉCUTÉ : verif/outils/axe.min.js absent.")
    axe_js = axe.read_text(encoding="utf-8")

    graves = []
    for largeur in LARGEURS_AUDITEES:
        page.set_viewport_size({"width": largeur, "height": 900})
        page.wait_for_timeout(400)
        for v in _violations_axe(page, axe_js):
            if v["impact"] in GRAVITES_REFUSEES:
                graves.append((largeur, v))
    page.set_viewport_size({"width": 1440, "height": 900})

    assert not graves, (
        "violations d'accessibilité serious ou critical :\n  "
        + "\n  ".join(
            f"[{largeur} px] [{v['impact']}] {v['id']} — {v['help']} · {v['noeuds']}"
            for largeur, v in graves
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


def test_une_action_garde_le_meme_nom_partout(html):
    """SPEC §7.3, et elle prend précisément cet exemple.

    Le guide avait deux verbes pour un seul geste : « Vérifier ma réponse » sur
    les vingt-sept exercices, « Valider ma réponse » sur les dix-sept questions
    du quiz, avec deux familles de retours derrière. Le stagiaire presse ce
    bouton quarante-quatre fois dans la journée ; qu'il change de nom au milieu
    lui fait croire que le geste change aussi.
    """
    import html as H

    visible = H.unescape(re.sub(r"<[^>]+>", " ", html))
    concurrents = []
    for verbe in ("Valider ma réponse", "Valider la réponse", "avant de valider"):
        if verbe in visible:
            concurrents.append(verbe)
    assert not concurrents, (
        "deux verbes pour la même action, alors que SPEC §7.3 exige « Vérifier "
        f"ma réponse » partout : {concurrents}"
    )
    assert "Vérifier ma réponse" in visible, (
        "le libellé de validation a disparu du guide"
    )


def test_aucun_balisage_markdown_visible(html):
    """Le balisage n'est pas du texte : il se rend, ou il n'a rien à faire là.

    Les consignes, les indices, les démarches et les propositions du quiz ne
    passent pas par le convertisseur Markdown — le gabarit les rend tels quels.
    Un « `event.code : \"4625\"` » écrit dans une proposition s'affichait donc
    avec ses accents graves, et, n'étant pas dans un <code>, la passe
    typographique y injectait des espaces insécables : la requête que le
    stagiaire recopiait de la BONNE réponse était fausse, sans que rien ne le
    signale. Dix accents graves figuraient aussi tels quels dans le quiz remis
    en salle.
    """
    visible = re.sub(r"<[^>]+>", " ", html)
    graves = visible.count("`")
    gras = visible.count("**")
    assert not graves, f"{graves} accent(s) grave(s) affiché(s) au stagiaire"
    assert not gras, f"{gras} balisage(s) de gras affiché(s) au stagiaire"


def test_le_texte_alternatif_de_chaque_capture_est_entier(html, plan_de_capture):
    """Un texte alternatif tronqué ne se voit pas : il faut le comparer au plan.

    La fabrique de figures interpolait sans échapper, là où le gabarit Jinja
    échappe tout seul. Le texte alternatif de M1-C1 contient « event.code :
    "4625" » : le guillemet droit refermait l'attribut, le navigateur tronquait
    l'alt au milieu d'une phrase et transformait la suite en seize attributs
    parasites. Le contrôle voisin ne voyait rien — il vérifie qu'un alt EXISTE.
    """
    import html as H

    manquants = []
    for capture in plan_de_capture:
        trouve = re.search(
            rf'data-capture="{re.escape(capture["id"])}".*?alt="([^"]*)"', html, re.S
        )
        if not trouve:
            continue
        publie = H.unescape(trouve.group(1))
        attendu = " ".join(str(capture["alt"]).split())
        if " ".join(publie.split()) != attendu:
            manquants.append(
                f"{capture['id']} : publié « {publie[:70]}… » pour « {attendu[:70]}… »"
            )
    assert not manquants, (
        "textes alternatifs publiés différents du plan de capture :\n  "
        + "\n  ".join(manquants)
    )


def test_aucune_entite_html_cassee(html):
    """La passe typographique ne doit pas disloquer les entités HTML.

    Le « ; » qui ferme une entité n'est pas une ponctuation. Sans garde, la
    règle « espace fine avant le point-virgule » transformait « l&#39;écran »
    en « l&#39<fine>; » — 1132 fois, jusque dans le sommaire et les titres
    d'exercices, où le lecteur voyait « Pourquoi l' ;écran est-il vide ».
    Aucun test ne regardait le HTML sous cet angle : la typographie était
    vérifiée sur le TEXTE extrait, où l'entité est déjà résolue et le défaut
    invisible.
    """
    cassees = re.findall(r"&[a-zA-Z0-9#x]{1,8}[   ];", html)
    assert not cassees, (
        f"{len(cassees)} entité(s) HTML disloquée(s) par la typographie, "
        f"par exemple {cassees[:3]}"
    )


# --------------------------------------------------------------------------
# Les captures : une image ne passe sous aucun garde de fuite
# --------------------------------------------------------------------------

# Les Spaces où vivent les réponses : les corrigés (titres et valeurs des
# tableaux de bord de M3 et M4) et le jeu de l'épreuve.
ESPACES_A_REPONSES = ("corriges", "epreuve")

# Unités de plage relative de Kibana, converties en jours.
_JOURS = {"s": 1 / 86400, "m": 1 / 1440, "h": 1 / 24, "d": 1, "w": 7, "M": 30, "y": 365}
_RELATIF = re.compile(r"^now(?:-(\d+)([smhdwMy]))?(?:/[smhdwMy])?$")


def _jours_avant_maintenant(expression: str) -> float | None:
    """« now-9y » → 3285 jours. None si l'expression n'est pas relative à « now »."""
    m = _RELATIF.match(expression.strip())
    if not m:
        return None
    if m.group(1) is None:
        return 0.0
    return int(m.group(1)) * _JOURS[m.group(2)]


@pytest.fixture(scope="module")
def plan_de_capture(config):
    chemin = config.RACINE / "captures" / "plan.yaml"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : captures/plan.yaml absent.")
    return yaml.safe_load(chemin.read_text(encoding="utf-8")) or []


def test_aucune_capture_du_guide_ne_montre_les_donnees_d_un_space_a_reponses(
    plan_de_capture, config
):
    """Une capture prise sur un corrigé publie des réponses en image.

    C'est par là qu'elles sont sorties. M3-C1 et M4-C1 étaient prises dans le
    Space « corriges », sur les tableaux de bord du corrigé, à la plage par
    défaut : les indicateurs affichaient les nombres attendus et les titres de
    panneaux étaient les questions elles-mêmes. Douze exercices se résolvaient
    en regardant le guide. Le garde de fuite de « outils/fuites.py » lit du
    texte ; il ne voit rien d'une image, et n'a rien signalé.

    Ces captures restent utiles — la STRUCTURE d'un tableau de bord s'enseigne
    mal sans image — mais elles doivent être prises sur une plage de temps
    prouvablement hors des données, de sorte que chaque panneau soit vide.
    D'où ce contrôle : toute capture visant un Space à réponses doit épingler
    dans son chemin une plage entièrement antérieure au jeu de données.
    """
    fenetre = float(config.valeur("donnees.fenetre_jours"))
    defauts = []

    for capture in plan_de_capture:
        espace = capture.get("espace")
        if espace not in ESPACES_A_REPONSES:
            continue
        identifiant = capture.get("id", "?")
        chemin = capture.get("chemin", "")

        m = re.search(r"time:\(from:([^,)]+),to:([^,)]+)\)", chemin)
        if not m:
            defauts.append(
                f"{identifiant} : vise le Space « {espace} » sans épingler de "
                "plage de temps — les panneaux afficheront les valeurs du corrigé"
            )
            continue

        debut, fin = (_jours_avant_maintenant(v.strip("'\"")) for v in m.groups())
        if debut is None or fin is None:
            defauts.append(
                f"{identifiant} : plage « {m.group(1)} → {m.group(2)} » non "
                "relative à « now » — impossible de prouver qu'elle est vide"
            )
            continue

        # « fin » est l'âge, en jours, de la BORNE HAUTE de la plage capturée :
        # elle doit être plus ancienne que le début du jeu de données.
        if fin <= fenetre:
            defauts.append(
                f"{identifiant} : la plage capturée remonte jusqu'à il y a "
                f"{fin:g} jour(s), alors que le jeu couvre les {fenetre:g} "
                "derniers jours — les panneaux ne seront pas vides"
            )
        elif debut < fin:
            defauts.append(
                f"{identifiant} : plage inversée ({debut:g} < {fin:g} jours)"
            )

    assert not defauts, (
        "captures susceptibles de publier des réponses en image :\n  "
        + "\n  ".join(defauts)
    )


def test_toutes_les_captures_du_plan_sont_dans_le_guide(plan_de_capture, html):
    """Le garde précédent ne vaut que s'il couvre bien les images publiées.

    Si une capture entrait dans le guide sans passer par le plan, elle
    échapperait au contrôle de plage ci-dessus. Les deux listes doivent donc
    coïncider.
    """
    attendues = [c["id"] for c in plan_de_capture]
    manquantes = [i for i in attendues if f"data-capture=\"{i}\"" not in html]
    assert not manquantes, (
        f"captures du plan absentes du guide : {manquantes} — lancez « make guide »"
    )

    publiees = set(re.findall(r'data-capture="([^"]+)"', html))
    hors_plan = sorted(publiees - set(attendues))
    assert not hors_plan, (
        f"images publiées sans passer par le plan de capture : {hors_plan}"
    )


# --------------------------------------------------------------------------
# Contraste des traits (WCAG 1.4.11)
# --------------------------------------------------------------------------

# Un trait qui délimite un composant doit atteindre 3:1 sur CE QU'IL BORDE.
# Le thème sombre tenait 3,49:1 sur le papier et passait pour conforme ; sur
# « --alerte-fond », il tombait à 2,95:1 — c'est-à-dire précisément sur les
# encadrés « piège », que seul leur trait distingue du texte courant.
FONDS_A_BORDER = ("--papier", "--papier-appui", "--alerte-fond", "--action-fond")
CONTRASTE_MINIMAL = 3.0


def _luminance(couleur: str) -> float:
    couleur = couleur.lstrip("#")
    if len(couleur) == 3:
        couleur = "".join(c * 2 for c in couleur)
    canaux = []
    for i in (0, 2, 4):
        c = int(couleur[i:i + 2], 16) / 255
        canaux.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canaux[0] + 0.7152 * canaux[1] + 0.0722 * canaux[2]


def _contraste(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    haut, bas = max(la, lb), min(la, lb)
    return (haut + 0.05) / (bas + 0.05)


def _themes(css: str) -> dict[str, dict[str, str]]:
    """Les jeux de variables du CSS : le clair (:root) et chaque thème sombre."""
    jeux: dict[str, dict[str, str]] = {}
    for nom, motif in (
        ("clair", r":root\s*\{(.*?)\}"),
        ("sombre (préférence système)",
         r"@media \(prefers-color-scheme: dark\)\s*\{\s*:root[^{]*\{(.*?)\}"),
        ("sombre (choisi)", r':root\[data-theme="sombre"\]\s*\{(.*?)\}'),
    ):
        m = re.search(motif, css, re.S)
        if not m:
            continue
        jeux[nom] = dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\s*;",
                                    m.group(1)))
    return jeux


def test_le_filet_atteint_trois_pour_un_sur_chaque_fond(config):
    """WCAG 1.4.11, mesuré sur tous les fonds — pas sur le seul papier."""
    css = (config.RACINE / "guide" / "styles" / "guide.css").read_text(encoding="utf-8")
    jeux = _themes(css)
    assert jeux, "aucun jeu de couleurs reconnu dans guide.css"

    defauts = []
    for nom, variables in jeux.items():
        filet = variables.get("--filet")
        if not filet:
            continue
        for fond in FONDS_A_BORDER:
            valeur = variables.get(fond)
            if not valeur:
                continue
            rapport = _contraste(filet, valeur)
            if rapport < CONTRASTE_MINIMAL:
                defauts.append(
                    f"thème {nom} : --filet {filet} sur {fond} {valeur} = "
                    f"{rapport:.2f}:1, sous {CONTRASTE_MINIMAL}:1"
                )

    assert not defauts, "traits sous le seuil de WCAG 1.4.11 :\n  " + "\n  ".join(defauts)


def test_le_sommaire_reste_atteignable_apres_avoir_defile(page_ouverte):
    """Un sommaire en tête d'un document de 107 000 px n'est pas un sommaire.

    MESURÉ : sous 62 rem, « .sommaire » était « position: static ». Arrivé au
    module M4, le stagiaire avait la barre de commande — sommaire, recherche,
    bascule de thème — à 29 230 px au-dessus de lui. Le seul moyen d'y revenir
    était de remonter tout le guide.

    Trois choses sont vérifiées, aux deux largeurs de téléphone usuelles : la
    bascule reste dans l'écran après un long défilement ; repliée, la barre ne
    mange pas la lecture ; et suivre un lien la replie, faute de quoi elle
    recouvrirait la section qu'on vient d'atteindre.
    """
    page, _ = page_ouverte
    defauts = []
    for largeur in (390, 320):
        page.set_viewport_size({"width": largeur, "height": 800})
        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.75)")
        page.wait_for_timeout(800)

        mesure = page.evaluate("""() => {
            const s = document.querySelector('.sommaire');
            const b = document.getElementById('bascule-sommaire');
            const rs = s.getBoundingClientRect();
            const rb = b.getBoundingClientRect();
            return {
              hauteur: Math.round(rs.height),
              bascule_dans_l_ecran: rb.top >= -1 && rb.bottom <= window.innerHeight + 1,
              defile: Math.round(window.scrollY),
            };
        }""")
        if not mesure["bascule_dans_l_ecran"]:
            defauts.append(
                f"{largeur} px : après {mesure['defile']} px de défilement, la "
                f"bascule du sommaire est hors de l'écran"
            )
        if mesure["hauteur"] > 0.4 * 800:
            defauts.append(
                f"{largeur} px : la barre repliée occupe {mesure['hauteur']} px "
                f"de haut et mange la lecture"
            )

        page.click("#bascule-sommaire")
        page.wait_for_timeout(500)
        if page.get_attribute(".sommaire", "data-ouvert") != "oui":
            defauts.append(f"{largeur} px : la bascule n'ouvre pas le sommaire")
        page.locator(".sommaire__module > a").first.click()
        page.wait_for_timeout(600)
        if page.get_attribute(".sommaire", "data-ouvert") != "non":
            defauts.append(
                f"{largeur} px : suivre un lien laisse le sommaire ouvert, donc "
                f"posé par-dessus la section atteinte"
            )

    page.set_viewport_size({"width": 1440, "height": 900})
    page.evaluate("window.scrollTo(0, 0)")
    assert not defauts, "sommaire sur téléphone :\n  " + "\n  ".join(defauts)


def test_la_recherche_surligne_ce_qu_elle_a_trouve(page_ouverte):
    """« 7 sections trouvées » laissait chercher le mot à l'œil dans sept sections.

    Le filtre masquait ce qui ne correspond pas, et s'arrêtait là. On exige
    donc un surlignage, et surtout qu'il s'EFFACE : un surlignage qui survit à
    l'effacement du champ salirait le guide jusqu'au rechargement.
    """
    page, _ = page_ouverte
    champ = page.locator("#recherche")
    champ.fill("cardinality")
    page.wait_for_timeout(900)
    poses = page.locator("mark.recherche__trouve").count()
    sections = page.locator("[data-cherchable]:not([hidden])").count()
    champ.fill("")
    page.wait_for_timeout(700)
    restants = page.locator("mark.recherche__trouve").count()
    rendues = page.locator("[data-cherchable]:not([hidden])").count()

    assert poses > 0, (
        f"« cardinality » retient {sections} section(s) mais n'est surligné nulle part"
    )
    assert restants == 0, f"{restants} surlignage(s) survivent à l'effacement du champ"
    assert rendues > sections, "effacer le champ ne rend pas les sections masquées"


def test_la_position_courante_descend_au_niveau_de_l_exercice(page_ouverte):
    """Le sommaire marquait toujours le module, jamais l'exercice lu.

    La section d'un module intersecte dès qu'un de ses exercices intersecte :
    en retenant la PREMIÈRE cible visible dans l'ordre du DOM, le module
    l'emportait toujours. Les trente-cinq entrées d'exercice du sommaire ne
    recevaient donc jamais « aria-current », et le repère s'arrêtait à « vous
    êtes quelque part dans M1 » — sur un module de 87 minutes.
    """
    page, _ = page_ouverte
    page.set_viewport_size({"width": 1440, "height": 900})
    exercices = page.locator("article.exercice[data-ancre]")
    assert exercices.count() > 6, "pas assez d'exercices pour mesurer"
    exercices.nth(6).scroll_into_view_if_needed()
    page.wait_for_timeout(1500)

    releve = page.evaluate("""() => {
        const a = document.querySelector('.sommaire a[aria-current="true"]');
        const m = document.querySelector('li.sommaire__module[data-courant="oui"] > a');
        return {courant: a ? a.getAttribute('href') : null,
                module: m ? m.getAttribute('href') : null};
    }""")
    page.evaluate("window.scrollTo(0, 0)")

    assert releve["courant"], "aucune entrée du sommaire n'est marquée courante"
    assert releve["courant"].startswith("#ex-"), (
        f"la position s'arrête au module : « {releve['courant']} »"
    )
    assert releve["module"], (
        "l'exercice est marqué mais son module ne l'est plus : le lecteur perd "
        "tout repère de module"
    )


def test_une_capture_agrandie_se_rend_a_sa_taille_reelle(page_ouverte):
    """Agrandie, la capture doublait la taille de l'écran qu'elle photographie.

    MESURÉ : 3 200 px de large, soit la taille intrinsèque du fichier. Or les
    captures sont prises à un facteur d'échelle de 2 sur une fenêtre de
    1 600 px : les rendre à 3 200 px, c'est un grossissement ×2 que personne
    n'a demandé, et un défilement horizontal deux fois plus long pour lire le
    même écran. « Agrandir » doit rendre la taille RÉELLE.
    """
    from verif.e2e.kibana import ECHELLE_DES_CAPTURES

    page, _ = page_ouverte
    page.set_viewport_size({"width": 1440, "height": 900})
    figure = page.locator("figure").first
    figure.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    figure.locator("button").first.click()
    page.wait_for_timeout(900)

    mesure = page.evaluate("""() => {
        const f = document.querySelector('figure[data-agrandi="oui"]');
        if (!f) return null;
        const i = f.querySelector('img');
        return {naturel: i.naturalWidth,
                rendu: Math.round(i.getBoundingClientRect().width)};
    }""")
    page.evaluate("window.scrollTo(0, 0)")
    assert mesure, "aucune figure ne s'est agrandie"
    attendu = round(mesure["naturel"] / ECHELLE_DES_CAPTURES)
    assert abs(mesure["rendu"] - attendu) <= 2, (
        f"capture agrandie rendue à {mesure['rendu']} px pour une taille réelle "
        f"de {attendu} px ({mesure['naturel']} px de fichier, échelle "
        f"{ECHELLE_DES_CAPTURES})"
    )


def test_le_contrat_de_design_est_tenu(config):
    """docs/DESIGN.md §« Contrat que le code devra respecter », vérifié.

    Un contrat qu'aucun contrôle ne relit dérive en silence : celui-ci
    interdisait toute « box-shadow » alors que l'infobulle du glossaire en
    portait une depuis P5, et réservait « --action » aux blocs d'action et au
    focus alors que les liens, le sommaire et le quiz s'en servaient. Le
    document a été rendu à ce que le kit fait vraiment ; ce contrôle empêche la
    dérive suivante.
    """
    css = (config.RACINE / "guide" / "styles" / "guide.css").read_text(encoding="utf-8")

    # Une seule ombre, celle de l'infobulle. « box-shadow: none » ne compte pas.
    ombres = [
        ligne.strip()
        for ligne in css.split("\n")
        if "box-shadow" in ligne and "none" not in ligne
    ]
    assert len(ombres) == 1, (
        f"{len(ombres)} box-shadow dans guide.css — le contrat n'en admet qu'une, "
        f"celle de l'infobulle du glossaire :\n  " + "\n  ".join(ombres)
    )

    # Aucun arrondi au-dessus de 4 px.
    trop_ronds = [
        f"{valeur}px"
        for valeur in re.findall(r"border-radius:\s*(\d+)px", css)
        if int(valeur) > 4
    ]
    assert not trop_ronds, (
        f"border-radius supérieurs à 4 px : {', '.join(sorted(set(trop_ronds)))}"
    )

    # La colonne de lecture, et le focus jamais supprimé.
    assert "--colonne: 68ch" in css, "la ligne de texte n'est plus bornée à 68ch"
    assert "outline: none" not in css.replace("outline: none;", "", css.count(
        "outline: none; /* remplacé"
    )), "un « outline: none » supprime un focus"

    # Les valeurs de la palette annoncées par DESIGN.md sont celles du CSS.
    design = (config.RACINE / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    # UNIQUEMENT la palette de la direction retenue : le document expose aussi
    # celle de la direction B, écartée, dont les valeurs ne sont pas au CSS —
    # et le contrôle les y cherchait.
    debut = design.index("### Palette — 5 couleurs nommées")
    design = design[debut:design.index("### Rôles typographiques", debut)]
    jeux = _themes(css)
    defauts = []
    for ligne in re.findall(r"^\|\s*`(--[\w-]+)`\s*\|\s*`(#[0-9a-fA-F]{6})`\s*\|"
                            r"\s*`(#[0-9a-fA-F]{6})`\s*\|", design, re.M):
        jeton, clair, sombre = ligne
        reel_clair = (jeux.get("clair") or {}).get(jeton)
        reel_sombre = (jeux.get("sombre (choisi)") or {}).get(jeton)
        if reel_clair and reel_clair.lower() != clair.lower():
            defauts.append(f"{jeton} clair : DESIGN.md dit {clair}, le CSS {reel_clair}")
        if reel_sombre and reel_sombre.lower() != sombre.lower():
            defauts.append(f"{jeton} sombre : DESIGN.md dit {sombre}, le CSS {reel_sombre}")
    assert not defauts, "la palette a dérivé de DESIGN.md :\n  " + "\n  ".join(defauts)
