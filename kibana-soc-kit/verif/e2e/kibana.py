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
    "indice_plage_de_temps": "discoverNoResultsTimefilter",
    "liste_des_champs": "fieldList",
    "selecteur_data_view": "discover-dataView-switch-link",
    # Sélecteur de temps. En 9.5 il s'appelle « dateRangePicker… » ; les noms
    # en « superDatePicker… » des versions précédentes n'existent plus, et les
    # employer ne lève aucune erreur : l'élément est simplement introuvable.
    # Relevé dans le lab le 21/09/2026.
    "selecteur_temps": "dateRangePickerControlButton",
    "valeur_temps": "dateRangePickerValueDisplay",
    "fenetre_temps": "dateRangePickerTimeWindowButtons",
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


def aller_a(page: Page, chemin: str, espace: str | None = None) -> None:
    """Navigue dans un Space, puis attend la fin du chargement.

    Par défaut le Space de formation ; les corrigés vivent dans le Space
    « corriges », d'où le paramètre.
    """
    espace = espace or str(conf.valeur("formation.space_id"))
    page.goto(f"{conf.url_kibana()}/s/{espace}{chemin}", wait_until="domcontentloaded")
    attendre_chargement(page)


def ouvrir_tableau_de_bord(page: Page, identifiant: str, espace: str | None = None) -> None:
    aller_a(page, f"/app/dashboards#/view/{identifiant}", espace=espace)
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


# --- Discover ---------------------------------------------------------------

def ouvrir_discover(page: Page, plage_debut: str = "now-7d", plage_fin: str = "now") -> None:
    """Ouvre Discover sur la data view du parcours, avec une plage explicite.

    La data view et la plage passent par l'état d'URL : ce sont des
    PRÉALABLES à l'exercice, pas ce qu'on veut éprouver. La requête, elle,
    sera bien saisie au clavier dans la barre de recherche.
    """
    data_view = str(conf.valeur("donnees.data_view_id"))
    etat_global = f"(time:(from:{plage_debut},to:{plage_fin}))"
    etat_app = f"(index:'{data_view}',query:(language:kuery,query:''))"
    aller_a(page, f"/app/discover#/?_g={etat_global}&_a={etat_app}")
    page.wait_for_selector(ts("barre_de_requete"), timeout=90_000)
    attendre_chargement(page)


def saisir_kql(page: Page, requete: str) -> None:
    """Saisit une requête KQL dans la barre de recherche, puis la soumet."""
    barre = page.locator(ts("barre_de_requete"))
    barre.click()
    barre.press("Control+a")
    barre.press("Delete")
    if requete:
        barre.type(requete, delay=8)
    # Entrée soumet la requête ; le bouton « Actualiser » fait de même et sert
    # de repli si la saisie n'a pas encore été prise en compte.
    barre.press("Enter")
    page.wait_for_timeout(1_500)
    attendre_chargement(page)
    page.wait_for_timeout(1_500)


def nombre_de_resultats(page: Page) -> int | None:
    """Nombre de documents affiché par Discover, ou 0 s'il annonce aucun résultat.

    Renvoie None si Discover n'affiche ni compteur ni message : l'appelant doit
    alors signaler un contrôle NON EXÉCUTÉ plutôt que de conclure à zéro.
    """
    if page.locator(ts("message_aucun_resultat")).count() > 0:
        return 0
    compteur = page.locator(ts("nombre_de_resultats"))
    if compteur.count() == 0:
        return None
    texte = compteur.first.inner_text()
    chiffres = "".join(c for c in texte if c.isdigit())
    return int(chiffres) if chiffres else None


def compter_avec_kql(page: Page, requete: str) -> int | None:
    """Tape une requête KQL dans Discover et renvoie le nombre de résultats."""
    saisir_kql(page, requete)
    return nombre_de_resultats(page)


def message_d_erreur_de_requete(page: Page) -> str | None:
    """Texte de l'erreur affichée par Discover, s'il y en a une.

    Sert à prouver les pièges du parcours : une syntaxe Lucene tapée en KQL ne
    donne pas toujours une erreur — parfois elle renvoie simplement autre chose
    que ce que le stagiaire croit demander (SPEC §6.3).
    """
    for selecteur in ('[data-test-subj="euiToastHeader"]', ".kbnQueryBar__textarea--invalid",
                      '[data-test-subj="queryBarErrorMessage"]'):
        element = page.locator(selecteur)
        if element.count() > 0:
            return element.first.inner_text()
    return None
