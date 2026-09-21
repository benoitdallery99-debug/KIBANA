"""Initialisation idempotente du lab : Space, rôles, comptes, data views.

Relançable sans effet de bord : chaque objet est créé s'il manque, mis à jour sinon.
Appelée par « make lab-up » et par « make lab-reset » (SPEC §4.3).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from outils import conf

TEMPS = 30


def entetes() -> dict[str, str]:
    return {"kbn-xsrf": "true", "Content-Type": "application/json"}


def kbn(methode: str, chemin: str, **kw: Any) -> requests.Response:
    return requests.request(
        methode,
        f"{conf.url_kibana()}{chemin}",
        auth=conf.auth_elastic(),
        headers=entetes(),
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


def space() -> None:
    """Space de formation, avec la vue de solution de kit.config.yaml."""
    space_id = str(conf.valeur("formation.space_id"))
    vue = str(conf.valeur("kibana.vue_solution"))
    corps = {
        "id": space_id,
        "name": "Formation SOC",
        "description": "Espace de formation Kibana pour analystes SOC",
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


def roles() -> None:
    """Deux rôles : le formateur pilote le Space, le stagiaire y travaille."""
    space_id = str(conf.valeur("formation.space_id"))
    motifs = [
        str(conf.valeur("donnees.data_view_motif")),
        str(conf.valeur("epreuve.data_view_motif")),
    ]

    etape(
        "Rôle « formateur »",
        kbn("PUT", "/api/security/role/formateur", json={
            "elasticsearch": {
                "cluster": ["monitor"],
                "indices": [{"names": motifs, "privileges": ["read", "view_index_metadata"]}],
            },
            # Tous droits, mais sur ce Space seulement.
            "kibana": [{"spaces": [space_id], "base": ["all"]}],
        }),
        attendus=(200, 204),
    )

    etape(
        "Rôle « stagiaire »",
        kbn("PUT", "/api/security/role/stagiaire", json={
            "elasticsearch": {
                # Lecture seule sur les données : un stagiaire n'altère jamais le jeu.
                "indices": [{"names": motifs, "privileges": ["read", "view_index_metadata"]}],
            },
            # Écriture des objets enregistrés du Space : il doit pouvoir construire
            # et sauvegarder ses recherches, visualisations et tableaux de bord.
            "kibana": [{"spaces": [space_id], "base": ["all"]}],
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
    """Data views à ID FIXE.

    L'ID fixe est le mécanisme qui rend les tableaux de bord du lab réutilisables sur
    la plateforme cible : il suffit d'y recréer une data view de même ID pointant le
    motif de production, et les objets importés se raccrochent (SPEC §4.3, module M5).
    """
    space_id = str(conf.valeur("formation.space_id"))
    for prefixe, libelle in (("donnees", "parcours"), ("epreuve", "épreuve pratique")):
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
            f"Data view « {dv_id} » → {motif}",
            kbn("POST", f"/s/{space_id}/api/data_views/data_view", json=corps),
        )


def main() -> int:
    print(f"Initialisation du lab — Kibana {conf.version()}, "
          f"locale {conf.valeur('kibana.locale')}, vue {conf.valeur('kibana.vue_solution')}")
    space()
    roles()
    comptes()
    data_views()
    print("Initialisation terminée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
