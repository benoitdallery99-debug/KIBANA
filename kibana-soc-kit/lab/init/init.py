"""Initialisation idempotente du lab : Spaces, rôles, comptes, data views.

Relançable sans effet de bord : chaque objet est créé s'il manque, mis à jour sinon.
Appelée par « make lab-up » et par « make lab-reset » (SPEC §4.3).

Quatre Spaces, et la séparation entre eux n'est pas décorative :

- « formation »  le Space de travail du stagiaire ;
- « reseau »     le Space de l'équipe voisine, cible de la copie de M3-E5 et de
                 l'import de M5-E3. Sans lui, ces deux exercices sont infaisables ;
- « corriges »   les tableaux de bord corrigés, visibles du FORMATEUR SEUL : leurs
                 titres et descriptions donnent les réponses de M3 et M4 ;
- « epreuve »    l'épreuve pratique, fermée par défaut. Le formateur l'ouvre par
                 « make epreuve-ouvrir » au moment de l'évaluation, et la referme.

De même pour les index : le rôle « stagiaire » ne lit QUE le motif du parcours.
Le jeu de l'épreuve lui reste inaccessible tant que le formateur n'a pas ouvert
l'épreuve — sinon le stagiaire pourrait préparer ses réponses toute la journée.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from outils import conf

TEMPS = 30

# PIÈGE MESURÉ EN LAB (9.5.3). « POST /api/kibana/settings » est documentée
# comme publique, mais elle répond
#   400 — « uri [/api/kibana/settings] with method [post] exists but is not
#   available with the current configuration »
# tant que l'appel ne se déclare pas d'origine interne. Le même appel avec cet
# en-tête répond 200. Relevé sur les deux routes, « /api/ » et « /internal/ ».
ORIGINE_INTERNE = {"x-elastic-internal-origin": "Kibana"}


def entetes() -> dict[str, str]:
    return {"kbn-xsrf": "true", "Content-Type": "application/json"}


def kbn(
    methode: str, chemin: str, entetes_sup: dict[str, str] | None = None, **kw: Any
) -> requests.Response:
    return requests.request(
        methode,
        f"{conf.url_kibana()}{chemin}",
        auth=conf.auth_elastic(),
        headers=entetes() | (entetes_sup or {}),
        timeout=TEMPS,
        **kw,
    )


def es(methode: str, chemin: str, **kw: Any) -> requests.Response:
    return requests.request(
        methode,
        f"{conf.url_es()}{chemin}",
        auth=conf.auth_elastic(),
        headers={"Content-Type": "application/json"},
        timeout=TEMPS,
        **kw,
    )


def etape(libelle: str, r: requests.Response, attendus: tuple[int, ...] = (200, 201)) -> None:
    if r.status_code in attendus:
        print(f"  [OK]    {libelle}")
        return
    if r.status_code == 409:
        print(f"  [DÉJÀ]  {libelle}")
        return
    raise SystemExit(f"  [ÉCHEC] {libelle} — HTTP {r.status_code} : {r.text[:400]}")


SPACE_RESEAU = "reseau"
SPACE_CORRIGES = "corriges"
SPACE_EPREUVE = "epreuve"


def _space(space_id: str, nom: str, description: str) -> None:
    """Crée ou met à jour un Space, avec la vue de solution de kit.config.yaml."""
    vue = str(conf.valeur("kibana.vue_solution"))
    corps = {
        "id": space_id,
        "name": nom,
        "description": description,
        # La vue de solution change toute la navigation depuis la 8.16 : elle doit
        # être identique à celle de la plateforme cible (SPEC §4.3).
        "solution": vue,
    }
    r = kbn("GET", f"/api/spaces/space/{space_id}")
    if r.status_code == 200:
        etape(f"Space « {space_id} » (vue de solution : {vue}) mis à jour",
              kbn("PUT", f"/api/spaces/space/{space_id}", json=corps))
    else:
        etape(f"Space « {space_id} » (vue de solution : {vue}) créé",
              kbn("POST", "/api/spaces/space", json=corps))


def spaces() -> None:
    _space(
        str(conf.valeur("formation.space_id")),
        "Formation SOC",
        "Espace de formation Kibana pour analystes SOC",
    )
    # Le Space de l'équipe voisine. M3-E5 y copie un tableau de bord, M5-E3 y
    # importe un ndjson : il doit exister AVANT que le stagiaire arrive dessus.
    _space(
        SPACE_RESEAU,
        "Équipe réseau",
        "Espace de l'équipe voisine — cible des copies et des imports du parcours",
    )
    # Réservé au formateur : les corrigés y vivent.
    _space(
        SPACE_CORRIGES,
        "Corrigés (formateur)",
        "Tableaux de bord corrigés — réservé au formateur",
    )
    _space(
        SPACE_EPREUVE,
        "Épreuve pratique",
        "Épreuve pratique — ouverte aux stagiaires par le formateur le moment venu",
    )


def roles() -> None:
    """Trois rôles, et le troisième ne sert que le temps de l'épreuve.

    Le découpage répond à une règle du kit : un stagiaire ne doit voir ni les
    corrigés, ni le jeu de l'épreuve, avant le moment prévu. Un rôle qui lit
    « logs-*-epreuve » toute la journée rendrait l'épreuve sans objet.
    """
    space_formation = str(conf.valeur("formation.space_id"))
    motif_parcours = str(conf.valeur("donnees.data_view_motif"))
    motif_epreuve = str(conf.valeur("epreuve.data_view_motif"))

    etape(
        "Rôle « formateur »",
        kbn("PUT", "/api/security/role/formateur", json={
            "elasticsearch": {
                "cluster": ["monitor"],
                "indices": [{
                    "names": [motif_parcours, motif_epreuve],
                    "privileges": ["read", "view_index_metadata"],
                }],
            },
            # Tous droits, sur les quatre Spaces du lab — corrigés compris.
            "kibana": [{
                "spaces": [space_formation, SPACE_RESEAU, SPACE_CORRIGES, SPACE_EPREUVE],
                "base": ["all"],
            }],
        }),
        attendus=(200, 204),
    )

    etape(
        "Rôle « stagiaire »",
        kbn("PUT", "/api/security/role/stagiaire", json={
            "elasticsearch": {
                # Lecture seule, et sur le SEUL motif du parcours : le jeu de
                # l'épreuve n'est pas lisible avec ce rôle.
                "indices": [{
                    "names": [motif_parcours],
                    "privileges": ["read", "view_index_metadata"],
                }],
            },
            # Écriture des objets enregistrés : il doit pouvoir construire et
            # sauvegarder ses recherches, visualisations et tableaux de bord.
            # Le Space « reseau » lui est ouvert, sans quoi la copie de M3-E5 et
            # l'import de M5-E3 n'ont aucune cible.
            "kibana": [{"spaces": [space_formation, SPACE_RESEAU], "base": ["all"]}],
        }),
        attendus=(200, 204),
    )

    etape(
        "Rôle « stagiaire-epreuve » (attribué par « make epreuve-ouvrir »)",
        kbn("PUT", "/api/security/role/stagiaire-epreuve", json={
            "elasticsearch": {
                "indices": [{
                    "names": [motif_epreuve],
                    "privileges": ["read", "view_index_metadata"],
                }],
            },
            "kibana": [{"spaces": [SPACE_EPREUVE], "base": ["all"]}],
        }),
        attendus=(200, 204),
    )


def comptes() -> None:
    s = conf.secrets()
    for nom, mdp, role in (
        ("formateur", s["FORMATEUR_PASSWORD"], "formateur"),
        ("stagiaire", s["STAGIAIRE_PASSWORD"], "stagiaire"),
    ):
        etape(
            f"Compte « {nom} »",
            es("PUT", f"/_security/user/{nom}", json={
                "password": mdp,
                "roles": [role],
                "full_name": nom.capitalize(),
            }),
        )


def data_views() -> None:
    """Data views à ID FIXE, chacune dans le Space qui la concerne.

    L'ID fixe est le mécanisme qui rend les tableaux de bord du lab réutilisables sur
    la plateforme cible : il suffit d'y recréer une data view de même ID pointant le
    motif de production, et les objets importés se raccrochent (SPEC §4.3, module M5).

    Celle du parcours vit dans le Space de formation. Celle de l'épreuve vit dans
    le Space de l'épreuve : la laisser dans le Space de formation afficherait au
    stagiaire, dès le sélecteur de source de Discover, l'existence du jeu caché.

    Le Space « reseau » n'en reçoit AUCUNE : la créer y est précisément l'exercice
    M5-E3, et la préparer d'avance le viderait de son objet.
    """
    space_formation = str(conf.valeur("formation.space_id"))
    dv_epreuve = str(conf.valeur("epreuve.data_view_id"))
    # Les premières versions du kit créaient la data view de l'épreuve dans le
    # Space de formation. Un lab existant la porte donc encore là, et Kibana
    # refuse alors de la créer ailleurs : « Saved object [...] conflict »
    # (relevé en lab, HTTP 400). On la retire d'abord du Space de formation —
    # où elle n'a rien à faire, puisqu'elle y annonçait au stagiaire, dans le
    # sélecteur de source de Discover, l'existence du jeu de l'épreuve.
    r = kbn("DELETE", f"/s/{space_formation}/api/saved_objects/index-pattern/{dv_epreuve}")
    if r.status_code == 200:
        print(f"  [OK]    Data view « {dv_epreuve} » retirée du Space « {space_formation} »")

    for prefixe, libelle, space_id in (
        ("donnees", "parcours", str(conf.valeur("formation.space_id"))),
        ("epreuve", "épreuve pratique", SPACE_EPREUVE),
    ):
        dv_id = str(conf.valeur(f"{prefixe}.data_view_id"))
        motif = str(conf.valeur(f"{prefixe}.data_view_motif"))
        corps = {
            "data_view": {
                "id": dv_id,
                "title": motif,
                "name": f"{motif} ({libelle})",
                "timeFieldName": "@timestamp",
                # Le lab s'initialise avant que les données soient chargées :
                # sans cette option, la création échouerait faute d'index.
                "allowNoIndex": True,
            },
            "override": True,
        }
        etape(
            f"Data view « {dv_id} » → {motif} (Space « {space_id} »)",
            kbn("POST", f"/s/{space_id}/api/data_views/data_view", json=corps),
        )


def fuseau_horaire() -> None:
    """Fixe le fuseau d'affichage de Kibana dans chaque Space.

    PIÈGE, et il coûtait deux réponses notées. Kibana laisse « dateFormat:tz »
    sur « Browser » : l'heure affichée est celle du POSTE du stagiaire. Or deux
    exercices font rendre une heure — M2-E6 demande l'heure la plus chargée,
    M4-E7 l'heure à laquelle la collecte reprend — et le manifeste calcule la
    réponse dans le fuseau métier. Sur un poste en UTC, l'écran affiche 8 et 12
    là où l'empreinte attend 10 et 14 : la réponse est refusée sans un mot
    d'explication, et le stagiaire cherche son erreur là où il n'y en a pas.

    Le contrôle ne pouvait pas l'attraper : la vérification pilote un navigateur
    dont le fuseau est forcé sur celui du métier. C'est l'écart entre le banc
    d'essai et la salle, exactement.
    """
    fuseau = str(conf.valeur("donnees.fuseau_metier"))
    for space_id in (
        str(conf.valeur("formation.space_id")),
        SPACE_RESEAU,
        SPACE_CORRIGES,
        SPACE_EPREUVE,
    ):
        etape(
            f"Fuseau d'affichage « {fuseau} » (Space « {space_id} »)",
            kbn(
                "POST",
                f"/s/{space_id}/api/kibana/settings",
                entetes_sup=ORIGINE_INTERNE,
                json={"changes": {"dateFormat:tz": fuseau}},
            ),
        )


def main() -> int:
    print(f"Initialisation du lab — Kibana {conf.version()}, "
          f"locale {conf.valeur('kibana.locale')}, vue {conf.valeur('kibana.vue_solution')}")
    spaces()
    fuseau_horaire()
    roles()
    comptes()
    data_views()
    print("Initialisation terminée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
