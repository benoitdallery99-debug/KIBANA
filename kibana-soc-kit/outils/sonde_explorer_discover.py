#!/usr/bin/env python3
"""Sonde : à quelles conditions « Explorer dans Discover » s'affiche-t-elle ?

docs/capacites.md, point Q : le passage d'un panneau vers Discover serait
refusé sur un panneau à plusieurs calques ou porteur d'un décalage temporel, et
exigerait le privilège « discover_v2.show ». **Aucun de ces trois points n'est
documenté.** Le parcours les enseignait pourtant comme des faits, et M4 en
faisait une question notée.

Cette sonde construit les cas dans le lab et relève ce que le menu montre. Elle
n'écrit rien dans le parcours : elle imprime un constat, qui est reporté à la
main dans docs/capacites.md et dans les modules.

    python3 outils/sonde_explorer_discover.py
"""

from __future__ import annotations

import json
import sys

import requests

from outils import conf
from verif.e2e import kibana as K

ESPACE = "corriges"
IDENTIFIANT = "sonde-explorer-discover"
LIBELLE = "Explorer dans Discover"

# Les cas, dans l'ordre où ils seront posés sur le tableau de bord. Le titre est
# ce qui permet de rattacher un panneau à son cas après rendu.
CAS = [
    ("temoin", "Cas temoin - une data view, un calque, aucun decalage"),
    ("deux_calques", "Cas deux calques"),
    ("decalage", "Cas decalage temporel"),
    ("esql", "Cas requete ES|QL"),
]


def kbn(methode: str, chemin: str, **kw) -> requests.Response:
    return requests.request(
        methode, f"{conf.url_kibana()}{chemin}",
        auth=conf.auth_elastic(),
        headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
        timeout=120, **kw,
    )


def _calque(decalage: str | None = None) -> dict:
    y: dict = {"operation": "count"}
    if decalage:
        y["time_shift"] = decalage
    calque: dict = {
        "type": "line",
        "data_source": {
            "type": "data_view_spec",
            "index_pattern": str(conf.valeur("donnees.data_view_motif")),
            "time_field": "@timestamp",
        },
        "x": {"operation": "date_histogram", "field": "@timestamp", "suggested_interval": "3h"},
        "y": [y],
    }
    return calque


def tableau() -> dict:
    motif = str(conf.valeur("donnees.data_view_motif"))
    # Quatre panneaux BAS, pour qu'ils tiennent tous dans la fenêtre du
    # navigateur de la sonde : un panneau hors écran n'affiche pas sa rangée
    # d'actions, et la sonde conclurait à une action refusée.
    grille = lambda i: {"x": 0, "y": i * 6, "w": 48, "h": 6}  # noqa: E731
    return {
        "title": "Sonde — conditions du passage vers Discover",
        "description": "Écran jetable. Voir outils/sonde_explorer_discover.py.",
        "tags": [],
        "time_range": {"from": "now-7d", "to": "now"},
        "panels": [
            {"grid": grille(0), "type": "vis", "config": {
                "type": "xy", "title": CAS[0][1], "layers": [_calque()]}},
            {"grid": grille(1), "type": "vis", "config": {
                "type": "xy", "title": CAS[1][1],
                "layers": [_calque(), _calque()]}},
            {"grid": grille(2), "type": "vis", "config": {
                "type": "xy", "title": CAS[2][1],
                "layers": [_calque(decalage="1d")]}},
            {"grid": grille(3), "type": "vis", "config": {
                "type": "data_table", "title": CAS[3][1],
                "data_source": {
                    "type": "esql",
                    "query": f"FROM {motif} | STATS n = COUNT(*) BY event.dataset",
                },
                "rows": [{"column": "event.dataset"}],
                "metrics": [{"column": "n"}],
            }},
        ],
    }


def poser() -> None:
    corps = tableau()
    r = kbn("PUT", f"/s/{ESPACE}/api/dashboards/{IDENTIFIANT}", json=corps)
    if r.status_code not in (200, 201):
        raise SystemExit(
            f"l'API Dashboards refuse la sonde : HTTP {r.status_code}\n{r.text[:1200]}"
        )
    print(f"sonde posée dans « {ESPACE} » (HTTP {r.status_code})")
    # Un décalage temporel silencieusement ignoré rendrait le cas « décalage »
    # identique au témoin, et le constat serait faux sans qu'on le voie.
    relu = kbn("GET", f"/s/{ESPACE}/api/dashboards/{IDENTIFIANT}")
    garde = "time_shift" in relu.text
    print(f"  décalage temporel conservé par l'API : {'oui' if garde else 'NON'}")
    if not garde:
        raise SystemExit(
            "l'API a effacé « time_shift » : le cas « décalage » ne prouverait rien."
        )


def retirer() -> None:
    kbn("DELETE", f"/s/{ESPACE}/api/saved_objects/dashboard/{IDENTIFIANT}")


SEL_ACTION = '[data-test-subj="embeddablePanelAction-ACTION_OPEN_IN_DISCOVER"]'

# Chemin relevé dans le DOM de 9.5.3 :
#   dashboardPanel#panel-<uuid>
#     > embeddablePanelHoverActions-<titre sans espaces>
#         > hover-actions-<uuid>  > … > embeddablePanelAction-<action>
#         > embeddablePanel        (ce que le kit appelle « panneau »)
# Les boutons d'action ne sont donc PAS dans l'élément « embeddablePanel », mais
# dans un FRÈRE, sous un ancêtre commun. Deux mesures s'y sont cassé les dents :
# les compter sur la page entière (ils y sont tous, pour tous les panneaux) et
# les rattacher par la géométrie (les rectangles de deux panneaux voisins se
# recouvrent à la tolérance près). On remonte à l'ancêtre, et on redescend.
ANCETRE = ("xpath=ancestor::*"
           "[starts-with(@data-test-subj,'embeddablePanelHoverActions-')][1]")


def _bouton_du_panneau(panneau):
    """Le bouton « Explorer dans Discover » de CE panneau, ou None."""
    bouton = panneau.locator(ANCETRE).locator(SEL_ACTION)
    return bouton.first if bouton.count() else None


def relever() -> dict[str, dict]:
    """Pour chaque panneau : l'action est-elle offerte, et où ?

    Relevé en lab : le bouton « Explorer dans Discover » n'est PAS dans le menu
    « … » du panneau. Il est dans la rangée d'actions rapides qui apparaît au
    survol, en haut à droite. La sonde regarde les deux endroits, parce que le
    parcours n'en cite qu'un — et cite le mauvais.
    """
    constat: dict[str, dict] = {}
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        K.ouvrir_tableau_de_bord(page, IDENTIFIANT, espace=ESPACE)

        panneaux = page.locator(K.ts("panneau"))
        total = panneaux.count()
        print(f"{total} panneau(x) rendus")
        for i in range(total):
            panneau = panneaux.nth(i)
            titre = panneau.locator(K.ts("titre_panneau")).first.inner_text().strip()

            panneau.scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            panneau.hover()
            page.wait_for_timeout(800)

            bouton = _bouton_du_panneau(panneau)
            entrees: list[str] = []
            try:
                page.get_by_label(f"Menu pour {titre}").click(timeout=15_000)
                page.wait_for_timeout(1_200)
                entrees = [
                    e.strip()
                    for e in page.locator(".euiContextMenuItem").all_inner_texts()
                ]
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
            except Exception as exc:  # la sonde consigne l'échec, elle ne casse pas
                entrees = [f"MENU INACCESSIBLE : {exc.__class__.__name__}"]

            constat[titre] = {
                "au_survol": bouton is not None,
                "dans_le_menu": any(LIBELLE in e for e in entrees),
                "entrees_du_menu": entrees,
                "aboutit": None,
            }

        # Deuxième passe : l'action est offerte, mais ABOUTIT-elle ? Une action
        # présente qui ouvrirait un Discover vide ou en erreur vaudrait, pour le
        # stagiaire, une action absente.
        for i in range(total):
            titre = list(constat)[i]
            if not constat[titre]["au_survol"]:
                continue
            K.ouvrir_tableau_de_bord(page, IDENTIFIANT, espace=ESPACE)
            panneau = page.locator(K.ts("panneau")).nth(i)
            panneau.scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            panneau.hover()
            page.wait_for_timeout(1_000)
            bouton = _bouton_du_panneau(panneau)
            try:
                # L'action ouvre Discover dans un NOUVEL ONGLET : attendre le
                # changement d'URL de la page courante ne rend jamais la main.
                with contexte.expect_page(timeout=30_000) as onglet:
                    bouton.click(timeout=15_000)
                vue = onglet.value
                vue.wait_for_load_state("domcontentloaded")
                K.attendre_chargement(vue)
                vue.wait_for_timeout(4_000)
                constat[titre]["aboutit"] = {
                    "url_discover": "/app/discover" in vue.url,
                    "resultats": K.nombre_de_resultats(vue),
                    "erreur": vue.locator(
                        '[data-test-subj="discoverErrorCalloutTitle"]'
                    ).count() > 0,
                }
                vue.close()
            except Exception as exc:
                constat[titre]["aboutit"] = {
                    "url_discover": False,
                    "echec": f"{exc.__class__.__name__}: {exc}"[:160],
                }

        # Troisième passe : le MÊME menu, en mode édition. Le parcours annonce
        # « Explorations » dans le menu du panneau ; en lecture, ce menu ne
        # compte que quatre entrées et celle-là n'y est pas. Reste à savoir si
        # elle apparaît quand l'écran est ouvert en modification.
        K.ouvrir_tableau_de_bord(page, IDENTIFIANT, espace=ESPACE)
        page.locator('[data-test-subj="dashboardEditMode"]').click(timeout=30_000)
        K.attendre_chargement(page)
        page.wait_for_timeout(3_000)
        panneaux = page.locator(K.ts("panneau"))
        for i in range(panneaux.count()):
            panneau = panneaux.nth(i)
            titre = panneau.locator(K.ts("titre_panneau")).first.inner_text().strip()
            panneau.scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            panneau.hover()
            page.wait_for_timeout(800)
            try:
                page.get_by_label(f"Menu pour {titre}").click(timeout=15_000)
                page.wait_for_timeout(1_200)
                entrees = [
                    e.strip()
                    for e in page.locator(".euiContextMenuItem").all_inner_texts()
                ]
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
            except Exception as exc:
                entrees = [f"MENU INACCESSIBLE : {exc.__class__.__name__}"]
            if titre in constat:
                constat[titre]["menu_en_edition"] = entrees
    return constat


def main() -> int:
    poser()
    try:
        constat = relever()
    finally:
        retirer()
        print("sonde retirée")

    print("\n=== CONSTAT ===")
    for titre, r in constat.items():
        survol = "survol:OUI " if r["au_survol"] else "survol:non "
        menu = "menu:OUI " if r["dans_le_menu"] else "menu:non "
        a = r.get("aboutit") or {}
        fin = ("aboutit" if a.get("url_discover") and not a.get("erreur")
               else "N'ABOUTIT PAS")
        print(f"  [{survol}{menu}] {fin:14s} {titre}")
    print("\n=== MENUS RELEVÉS ===")
    print(json.dumps(constat, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
