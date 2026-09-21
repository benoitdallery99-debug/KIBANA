"""Sonde les capacités réellement offertes par le lab — SPEC §4.5, phase P1.

La documentation dit ce qui devrait exister ; le lab dit ce qui existe. Pour la
moitié des capacités, la documentation ne précise pas le niveau d'abonnement :
c'est cette sonde qui tranche, en interrogeant l'instance elle-même.

Écrit docs/capacites-lab.json. Aucune supposition : ce qui n'a pas pu être testé
est marqué « non testé » avec sa raison (CLAUDE.md, statuts honnêtes).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf

ESPACE = None  # rempli dans main()


def kbn(methode: str, chemin: str, **kw) -> requests.Response:
    return requests.request(
        methode, f"{conf.url_kibana()}{chemin}",
        auth=conf.auth_elastic(),
        headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
        timeout=90, **kw,
    )


def es(methode: str, chemin: str, **kw) -> requests.Response:
    return requests.request(
        methode, f"{conf.url_es()}{chemin}",
        auth=conf.auth_elastic(),
        headers={"Content-Type": "application/json"},
        timeout=90, **kw,
    )


def licence() -> dict[str, Any]:
    d = es("GET", "/_license").json()["license"]
    return {"type": d["type"], "statut": d["status"]}


def connecteurs() -> list[dict]:
    """Connecteurs d'alerte, avec le niveau d'abonnement exigé par chacun.

    Attendu en Basic : Index et Server log seulement (SPEC §4.5).
    """
    r = kbn("GET", "/api/actions/connector_types")
    if r.status_code != 200:
        return [{"erreur": f"HTTP {r.status_code}"}]
    return sorted(
        (
            {
                "id": c["id"],
                "nom": c.get("name"),
                "licence_minimale": c.get("minimum_license_required"),
                "utilisable_avec_cette_licence": c.get("enabled_in_license"),
            }
            for c in r.json()
        ),
        key=lambda c: (not c["utilisable_avec_cette_licence"], c["id"]),
    )


def types_de_regles() -> list[dict]:
    r = kbn("GET", "/api/alerting/rule_types")
    if r.status_code != 200:
        return [{"erreur": f"HTTP {r.status_code}"}]
    return sorted(
        (
            {
                "id": t["id"],
                "nom": t.get("name"),
                "licence_minimale": t.get("minimum_license_required"),
                "utilisable_avec_cette_licence": t.get("enabled_in_license"),
                "categorie": t.get("category"),
                "produit": t.get("producer"),
            }
            for t in r.json()
        ),
        key=lambda t: (not t["utilisable_avec_cette_licence"], t["id"]),
    )


def fonctionnalites() -> list[dict]:
    """Fonctionnalités attribuables par Space (privilèges par fonctionnalité)."""
    r = kbn("GET", "/api/features")
    if r.status_code != 200:
        return [{"erreur": f"HTTP {r.status_code}"}]
    return sorted(
        (
            {
                "id": f["id"],
                "nom": f.get("name"),
                "licence_minimale": f.get("minimumLicense", "basic"),
                "categorie": (f.get("category") or {}).get("label"),
            }
            for f in r.json()
        ),
        key=lambda f: f["id"],
    )


def api_dashboards() -> dict:
    """L'API Dashboards est-elle réellement servie, et en licence Basic ?

    Le contrôle crée un tableau de bord jetable puis le supprime : c'est la
    seule preuve qui vaille, un simple GET pouvant répondre sur une route
    enregistrée mais non fonctionnelle.
    """
    # Les routes sont « POST /api/dashboards » et « PUT /api/dashboards/{id} ».
    # La doc recommande le PUT avec un identifiant choisi : il est idempotent,
    # alors qu'un POST engendre un nouvel identifiant à chaque appel — ce qui
    # est exactement ce qu'il faut pour rejouer un tableau de bord versionné.
    identifiant = "kit-soc-sonde-api-dashboards"
    corps = {
        "title": "Sonde API Dashboards (jetable)",
        "description": "Créé puis supprimé par lab/sonder_capacites.py",
        "panels": [],
    }
    cree = kbn("PUT", f"/s/{ESPACE}/api/dashboards/{identifiant}", json=corps)
    resultat: dict[str, Any] = {
        "creation_http": cree.status_code,
        "servie": cree.status_code in (200, 201),
    }
    if not resultat["servie"]:
        resultat["detail"] = cree.text[:300]
        return resultat

    lu = kbn("GET", f"/s/{ESPACE}/api/dashboards/{identifiant}")
    resultat["relecture_http"] = lu.status_code
    resultat["format_json_diffable"] = lu.status_code == 200 and "data" in lu.json()
    liste = kbn("GET", f"/s/{ESPACE}/api/dashboards")
    resultat["liste_http"] = liste.status_code
    supprime = kbn("DELETE", f"/s/{ESPACE}/api/dashboards/{identifiant}")
    resultat["suppression_http"] = supprime.status_code
    resultat["nettoye"] = supprime.status_code in (200, 204)
    resultat["licence_suffisante"] = "basic — créé, relu et supprimé sans erreur"
    return resultat


def esql() -> dict:
    """ES|QL est-il disponible côté Elasticsearch, et depuis Kibana ?"""
    motif = f"logs-*-{conf.valeur('donnees.namespace')}"
    requete = {"query": f"FROM {motif} | STATS n = COUNT(*) | LIMIT 1"}
    direct = es("POST", "/_query?format=json", json=requete)
    par_kibana = kbn("POST", "/api/console/proxy?path=_query&method=POST", json=requete)
    resultat = {
        "elasticsearch_http": direct.status_code,
        "disponible": direct.status_code == 200,
        "par_kibana_http": par_kibana.status_code,
    }
    if direct.status_code == 200:
        resultat["exemple_resultat"] = direct.json().get("values")
    else:
        resultat["detail"] = direct.text[:300]
    return resultat


def rapports() -> dict:
    """Rapports PDF/PNG : attendus INDISPONIBLES en Basic (SPEC §4.5).

    On lit ce que Kibana déclare lui-même, plutôt que de supposer.
    """
    r = kbn("GET", "/api/reporting/diagnose/screenshot")
    types = kbn("GET", "/api/reporting/jobs/list")
    return {
        "diagnostic_capture_http": r.status_code,
        "liste_travaux_http": types.status_code,
        "detail": r.text[:300] if r.status_code != 200 else "diagnostic accessible",
    }


def export_csv_et_objets() -> dict:
    """Export des objets enregistrés (ndjson) : la base de M5."""
    r = kbn(
        "POST", f"/s/{ESPACE}/api/saved_objects/_export",
        json={"type": ["index-pattern"], "excludeExportDetails": False},
    )
    return {
        "export_ndjson_http": r.status_code,
        "disponible": r.status_code == 200,
        "taille_octets": len(r.content) if r.status_code == 200 else 0,
    }


def terminologie() -> dict:
    """Vocabulaire EXACT de la version, relevé dans les traductions servies.

    Le guide doit employer les libellés que le stagiaire a sous les yeux, dans
    la locale de kit.config.yaml — jamais une traduction faite de tête.
    """
    locale = str(conf.valeur("kibana.locale"))
    r = kbn("GET", f"/translations/{locale}.json")
    if r.status_code != 200:
        return {"erreur": f"HTTP {r.status_code}"}
    messages = r.json().get("messages", {})

    def libelle(cle: str) -> str | None:
        valeur = messages.get(cle)
        if isinstance(valeur, dict):
            return valeur.get("text")
        return valeur

    interessants = {
        "session_discover": "discover.savedSearch.savedObjectName",
        "data_view_singulier": "dataViews.savedObjectName",
        "tableaux_de_bord": "dashboard.dashboardPageTitle",
        "section_pliable": "dashboard.collapsibleSection.displayName",
        "telecharger_csv": "dashboard.actions.DownloadCreateDrilldownAction.displayName",
    }
    return {
        "locale": locale,
        "nombre_de_cles": len(messages),
        "libelles": {nom: libelle(cle) for nom, cle in interessants.items()},
    }


def main() -> int:
    global ESPACE
    ESPACE = str(conf.valeur("formation.space_id"))

    sonde = {
        "version_stack": conf.version(),
        "licence": licence(),
        "espace": ESPACE,
        "avertissement": (
            "Relevé sur le lab, instance réelle en licence Basic. Fait foi sur la "
            "documentation en cas de divergence (CLAUDE.md)."
        ),
        "api_dashboards": api_dashboards(),
        "esql": esql(),
        "export_objets_enregistres": export_csv_et_objets(),
        "rapports": rapports(),
        "connecteurs": connecteurs(),
        "types_de_regles": types_de_regles(),
        "fonctionnalites_par_space": fonctionnalites(),
        "terminologie": terminologie(),
    }

    sortie = conf.RACINE / "docs" / "capacites-lab.json"
    sortie.write_text(json.dumps(sonde, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lic = sonde["licence"]
    print(f"Licence : {lic['type']} ({lic['statut']})")
    print(f"API Dashboards servie   : {sonde['api_dashboards']['servie']} "
          f"(création HTTP {sonde['api_dashboards']['creation_http']})")
    print(f"ES|QL disponible        : {sonde['esql']['disponible']}")
    utilisables = [c for c in sonde["connecteurs"] if c.get("utilisable_avec_cette_licence")]
    print(f"Connecteurs utilisables : {len(utilisables)} / {len(sonde['connecteurs'])} "
          f"→ {[c['id'] for c in utilisables]}")
    regles = [t for t in sonde["types_de_regles"] if t.get("utilisable_avec_cette_licence")]
    print(f"Types de règles         : {len(regles)} / {len(sonde['types_de_regles'])} utilisables")
    print(f"Écrit : {sortie.relative_to(conf.RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
