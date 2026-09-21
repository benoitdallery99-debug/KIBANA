"""Pilotage de Kibana par Playwright — module UNIQUE des sélecteurs (SPEC §7.2).

Tous les sélecteurs de l'interface sont centralisés ici : après une montée de
version, c'est le seul fichier à reprendre. Ils s'appuient sur l'attribut
« data-test-subj », stable d'une version à l'autre et indépendant de la langue
— contrairement aux libellés, qui dépendent de kibana.locale.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from outils import conf

# Chromium fourni par l'environnement de fabrication. Playwright téléchargerait
# sinon sa propre version : la chaîne de fabrication n'a pas à le faire.
CHROMIUM = os.environ.get(
    "KIT_CHROMIUM", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
)

# --- Sélecteurs, par écran --------------------------------------------------
SEL = {
    # Connexion
    "identifiant": "loginUsername",
    "mot_de_passe": "loginPassword",
    "valider_connexion": "loginSubmit",
    # Chrome applicatif
    "chargement_termine": "globalLoadingIndicator-hidden",
    "menu_navigation": "toggleNavButton",
    # Discover
    "barre_de_requete": "queryInput",
    "bouton_rafraichir": "querySubmitButton",
    "nombre_de_resultats": "discoverQueryHits",
    "message_aucun_resultat": "discoverNoResults",
    "liste_des_champs": "fieldList",
    "selecteur_data_view": "discover-dataView-switch-link",
    # Sélecteur de temps
    "selecteur_temps": "superDatePickerToggleQuickMenuButton",
    "temps_debut": "superDatePickerstartDatePopoverButton",
    "appliquer_temps": "superDatePickerApplyTimeButton",
    # Tableaux de bord
    "panneau": "embeddablePanel",
    "titre_panneau": "dashboardPanelTitle",
    "erreur_panneau": "embeddableStackTrace",
    "page_liste_tableaux": "dashboardLandingPage",
}


def ts(nom: str) -> str:
    """Sélecteur CSS à partir du nom logique d'un élément."""
    return f'[data-test-subj="{SEL[nom]}"]'


@contextmanager
def navigateur(entetes: bool = False):
    """Ouvre un navigateur configuré comme l'exige SPEC §7.2.

    Locale de kit.config.yaml, fuseau Europe/Paris, facteur d'échelle 2 : les
    captures doivent montrer au stagiaire exactement ce qu'il verra.
    """
    with sync_playwright() as p:
        lanceur = p.chromium.launch(
            executable_path=CHROMIUM if Path(CHROMIUM).exists() else None,
            headless=not entetes,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        contexte = lanceur.new_context(
            locale=str(conf.valeur("kibana.locale")),
            timezone_id=str(conf.valeur("donnees.fuseau_metier")),
            viewport={"width": 1600, "height": 1000},
            device_scale_factor=2,
        )
        contexte.set_default_timeout(60_000)
        try:
            yield contexte
        finally:
            contexte.close()
            lanceur.close()


def connexion(page: Page, identifiant: str | None = None, secret: str | None = None) -> None:
    """Ouvre une session. Par défaut le compte « elastic » (fabrication)."""
    secrets = conf.secrets()
    identifiant = identifiant or "elastic"
    secret = secret or secrets["ELASTIC_PASSWORD"]

    page.goto(f"{conf.url_kibana()}/login", wait_until="domcontentloaded")
    page.wait_for_selector(ts("identifiant"))
    page.fill(ts("identifiant"), identifiant)
    page.fill(ts("mot_de_passe"), secret)
    page.click(ts("valider_connexion"))
    page.wait_for_url(lambda url: "/login" not in url, timeout=90_000)
    attendre_chargement(page)


def attendre_chargement(page: Page, delai: int = 90_000) -> None:
    """Attend la fin du chargement global.

    Capturer avant la fin du chargement donnerait des écrans à moitié peints
    (CLAUDE.md). Subtilité relevée en lab : l'élément
    « globalLoadingIndicator-hidden » est TOUJOURS présent dans le DOM, mais
    masqué en CSS. L'attendre « visible » n'aboutit donc jamais ; c'est son
    rattachement au DOM qu'il faut attendre.
    """
    page.wait_for_selector(ts("chargement_termine"), state="attached", timeout=delai)


def aller_a(page: Page, chemin: str) -> None:
    """Navigue dans le Space de formation, puis attend la fin du chargement."""
    espace = str(conf.valeur("formation.space_id"))
    page.goto(f"{conf.url_kibana()}/s/{espace}{chemin}", wait_until="domcontentloaded")
    attendre_chargement(page)


def ouvrir_tableau_de_bord(page: Page, identifiant: str) -> None:
    aller_a(page, f"/app/dashboards#/view/{identifiant}")
    page.wait_for_selector(ts("panneau"), timeout=90_000)
    attendre_chargement(page)
    # Les panneaux se peignent après la fin du chargement global : on laisse le
    # rendu se stabiliser avant tout constat.
    page.wait_for_timeout(4_000)


def panneaux_en_erreur(page: Page) -> list[str]:
    """Titres des panneaux qui affichent une erreur de rendu."""
    en_erreur = []
    panneaux = page.locator(ts("panneau"))
    for i in range(panneaux.count()):
        panneau = panneaux.nth(i)
        if panneau.locator(ts("erreur_panneau")).count() > 0:
            titre = panneau.locator(ts("titre_panneau"))
            en_erreur.append(titre.inner_text() if titre.count() else f"panneau #{i}")
    return en_erreur


def textes_des_panneaux(page: Page) -> list[str]:
    panneaux = page.locator(ts("panneau"))
    return [panneaux.nth(i).inner_text() for i in range(panneaux.count())]
