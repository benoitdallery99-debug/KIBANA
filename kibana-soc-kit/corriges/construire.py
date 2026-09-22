"""Construit les deux tableaux de bord corrigés — SPEC §6.2 (M4) et P4.

« Santé de la collecte » et « Vue IDS ». Ils sont définis EN CODE, par l'API
Dashboards (GA en 9.5, servie en licence Basic — confirmé sur le lab), puis
exportés en ndjson : le kit livre donc les deux formats exigés par P4.

Règles de conception appliquées (SPEC §6.2, module M3) :
- un tableau de bord = un public + une question ;
- les indicateurs clés en haut à gauche ;
- au plus douze panneaux ;
- des titres formulés en questions ;
- pas de secteurs au-delà de cinq parts.

Contrainte relevée sur le lab : l'API Dashboards n'accepte pas de référence à
une data view par son identifiant (« data_view » est refusé, seul
« data_view_spec » est admis). Conséquence, que le module M5 enseigne et qu'il
faut écrire ici sans l'adoucir : un écran défini par cette API n'a AUCUNE
référence, et son export ndjson n'en a pas davantage — il porte des data views
ad hoc et le motif d'index en ligne. Ce n'est donc pas l'export qui rend l'écran
portable : pour la plateforme cible, c'est le MOTIF qu'on change dans le
fichier. Seule la voie « construit dans l'interface, puis exporté » produit une
référence vers une data view à identifiant fixe, et le kit ne l'emprunte pas ici.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf

COULEUR_OK = "#24c292"
COULEUR_ALERTE = "#f6726a"
COULEUR_ATTENTION = "#fcd883"


def source_donnees(motif_index: str | None = None) -> dict:
    """Source de données d'un panneau : le motif du kit, jamais écrit en dur.

    L'API Dashboards n'admet pas de filtre au niveau du panneau (« filter » est
    refusé, constaté en lab). Pour restreindre un panneau à une source, on vise
    donc directement le motif d'index de cette source — ce qui est de toute
    façon plus lisible qu'un filtre caché dans un panneau.
    """
    return {
        "type": "data_view_spec",
        "index_pattern": motif_index or str(conf.valeur("donnees.data_view_motif")),
        "time_field": "@timestamp",
    }


def esql(requete: str) -> dict:
    return {"type": "esql", "query": requete}


def motif() -> str:
    return str(conf.valeur("donnees.data_view_motif"))


# ---------------------------------------------------------------------------
# Tableau de bord 1 — Santé de la collecte
# ---------------------------------------------------------------------------

def sante_de_la_collecte() -> dict:
    m = motif()
    return {
        "title": "Santé de la collecte",
        "description": (
            "Public : le chef de salle. Question : mes sources envoient-elles toutes, "
            "et sans interruption ? Tableau de bord corrigé du module M4."
        ),
        "tags": [],
        "time_range": {"from": "now-7d", "to": "now"},
        "panels": [
            # Indicateurs clés, en haut à gauche.
            {
                "grid": {"x": 0, "y": 0, "w": 12, "h": 6},
                "type": "vis",
                "config": {
                    "type": "metric",
                    "title": "Combien d'événements sur la période ?",
                    "data_source": source_donnees(),
                    "metrics": [{
                        "type": "primary", "operation": "count",
                        "label": "Événements collectés",
                        "format": {"type": "number", "decimals": 0},
                        "background_chart": {"type": "trend"},
                    }],
                },
            },
            {
                "grid": {"x": 12, "y": 0, "w": 12, "h": 6},
                "type": "vis",
                "config": {
                    "type": "metric",
                    "title": "Combien de sources ont émis dans la dernière heure ?",
                    # Compté sur la DERNIÈRE HEURE, et non sur toute la période :
                    # sur sept jours, une source tue depuis deux heures compte
                    # encore, et l'indicateur resterait au vert. C'est tout
                    # l'objet du scénario S6.
                    "data_source": esql(
                        f"FROM {m} | WHERE @timestamp > NOW() - 1 hour "
                        "| STATS sources = COUNT_DISTINCT(event.dataset)"
                    ),
                    "metrics": [{
                        "type": "primary", "column": "sources",
                        "label": "Sources actives (1 h)",
                        # Six sources attendues : en dessous, une source s'est tue.
                        "color": {
                            "type": "dynamic", "range": "absolute",
                            "steps": [
                                {"lt": 6, "color": COULEUR_ALERTE},
                                {"gte": 6, "color": COULEUR_OK},
                            ],
                        },
                        "apply_color_to": "background",
                    }],
                },
            },
            # Le volume par source dans le temps : c'est là que se voit le trou (S5).
            {
                "grid": {"x": 24, "y": 0, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "xy",
                    "title": "Le volume de chaque source tient-il dans le temps ?",
                    "layers": [{
                        "type": "bar_stacked",
                        "data_source": source_donnees(),
                        "x": {"operation": "date_histogram", "field": "@timestamp"},
                        "y": [{"operation": "count"}],
                        "breakdown_by": {
                            "operation": "terms", "fields": ["event.dataset"], "limit": 8,
                        },
                    }],
                },
            },
            # Le panneau décisif : « dernier événement vu par source ».
            # Une source muette ne produit AUCUN bucket ; elle disparaîtrait d'un
            # simple décompte. En raisonnant sur le dernier événement vu, elle
            # reste visible — et se place en tête du tri.
            {
                "grid": {"x": 0, "y": 6, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "data_table",
                    "title": "Quand chaque source a-t-elle émis pour la dernière fois ?",
                    "data_source": esql(
                        f"FROM {m} "
                        "| STATS dernier_evenement = MAX(@timestamp), volume = COUNT(*) "
                        "BY source = event.dataset "
                        "| SORT dernier_evenement ASC"
                    ),
                    "rows": [{"column": "source"}, {"column": "dernier_evenement"}],
                    "metrics": [{"column": "volume"}],
                },
            },
            {
                "grid": {"x": 0, "y": 18, "w": 48, "h": 11},
                "type": "vis",
                "config": {
                    "type": "xy",
                    "title": "Le rythme horaire de la collecte est-il régulier ?",
                    "layers": [{
                        "type": "line",
                        "data_source": source_donnees(),
                        "x": {"operation": "date_histogram", "field": "@timestamp"},
                        "y": [{"operation": "count"}],
                    }],
                },
            },
        ],
    }


# ---------------------------------------------------------------------------
# Tableau de bord 2 — Vue IDS
# ---------------------------------------------------------------------------

def vue_ids() -> dict:
    m = motif()
    alertes = f"{m.replace('logs-*', 'logs-ids.alert')}"
    return {
        "title": "Vue IDS",
        "description": (
            "Public : l'analyste de permanence. Question : que me signale la sonde IDS, "
            "et par où commencer ? Tableau de bord corrigé du module M4."
        ),
        "tags": [],
        "time_range": {"from": "now-7d", "to": "now"},
        "panels": [
            {
                "grid": {"x": 0, "y": 0, "w": 12, "h": 6},
                "type": "vis",
                "config": {
                    "type": "metric",
                    "title": "Combien d'alertes sur la période ?",
                    "data_source": source_donnees(alertes),
                    "metrics": [{
                        "type": "primary", "operation": "count",
                        "label": "Alertes IDS",
                        "background_chart": {"type": "trend"},
                    }],
                },
            },
            {
                "grid": {"x": 12, "y": 0, "w": 12, "h": 6},
                "type": "vis",
                "config": {
                    "type": "metric",
                    "title": "Combien de signatures distinctes ?",
                    "data_source": source_donnees(alertes),
                    "metrics": [{
                        "type": "primary", "operation": "unique_count", "field": "rule.name",
                        "label": "Signatures distinctes",
                    }],
                },
            },
            {
                "grid": {"x": 24, "y": 0, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "xy",
                    "title": "Comment les alertes se répartissent-elles par gravité ?",
                    "layers": [{
                        "type": "bar_stacked",
                        "data_source": esql(
                            f"FROM {alertes} "
                            "| STATS alertes = COUNT(*) BY gravite = event.severity "
                            "| SORT gravite ASC"
                        ),
                        "x": {"column": "gravite"},
                        "y": [{"column": "alertes"}],
                    }],
                },
            },
            # M4-O2 et la consigne de M4-E2 demandent la gravité DANS LE TEMPS,
            # et l'écran n'en montrait que la répartition : un pic de gravité 4
            # à trois heures du matin y était indiscernable d'une gravité 4
            # étalée sur la semaine. C'est pourtant la première chose que
            # l'analyste de permanence regarde.
            {
                "grid": {"x": 0, "y": 6, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "xy",
                    "title": "Comment la gravité évolue-t-elle au fil du temps ?",
                    "layers": [{
                        "type": "bar_stacked",
                        "data_source": source_donnees(alertes),
                        "x": {"operation": "date_histogram", "field": "@timestamp"},
                        "y": [{"operation": "count"}],
                        # Le générateur ne produit que quatre gravités : la
                        # limite 5 n'en coupe aucune.
                        "breakdown_by": {
                            "operation": "terms", "fields": ["event.severity"], "limit": 5,
                        },
                    }],
                },
            },
            {
                "grid": {"x": 0, "y": 18, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "data_table",
                    "title": "Quelles signatures se déclenchent le plus ?",
                    "data_source": esql(
                        f"FROM {alertes} "
                        "| STATS alertes = COUNT(*), gravite_max = MAX(event.severity) "
                        "BY signature = rule.name "
                        "| SORT alertes DESC | LIMIT 10"
                    ),
                    "rows": [{"column": "signature"}],
                    "metrics": [{"column": "alertes"}, {"column": "gravite_max"}],
                },
            },
            {
                "grid": {"x": 24, "y": 12, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "data_table",
                    "title": "Quelles sources déclenchent le plus d'alertes ?",
                    "data_source": esql(
                        f"FROM {alertes} "
                        "| STATS alertes = COUNT(*), signatures = COUNT_DISTINCT(rule.name) "
                        "BY source = source.ip "
                        "| SORT alertes DESC | LIMIT 10"
                    ),
                    "rows": [{"column": "source"}],
                    "metrics": [{"column": "alertes"}, {"column": "signatures"}],
                },
            },
            {
                "grid": {"x": 0, "y": 30, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "data_table",
                    "title": "Quelles destinations sont les plus visées ?",
                    "data_source": esql(
                        f"FROM {alertes} "
                        "| STATS alertes = COUNT(*) BY destination = destination.ip "
                        "| SORT alertes DESC | LIMIT 10"
                    ),
                    "rows": [{"column": "destination"}],
                    "metrics": [{"column": "alertes"}],
                },
            },
            {
                "grid": {"x": 24, "y": 24, "w": 24, "h": 12},
                "type": "vis",
                "config": {
                    "type": "data_table",
                    "title": "Quelles sont les dernières alertes reçues ?",
                    "data_source": esql(
                        f"FROM {alertes} "
                        "| SORT @timestamp DESC "
                        "| KEEP @timestamp, rule.name, source.ip, destination.ip, event.severity "
                        "| LIMIT 20"
                    ),
                    "rows": [
                        {"column": "@timestamp"}, {"column": "rule.name"},
                        {"column": "source.ip"}, {"column": "destination.ip"},
                    ],
                    "metrics": [{"column": "event.severity"}],
                },
            },
        ],
    }


TABLEAUX = {
    "kit-soc-sante-collecte": sante_de_la_collecte,
    "kit-soc-vue-ids": vue_ids,
}


# ---------------------------------------------------------------------------

def kbn(methode: str, chemin: str, **kw) -> requests.Response:
    return requests.request(
        methode, f"{conf.url_kibana()}{chemin}",
        auth=conf.auth_elastic(),
        headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
        timeout=120, **kw,
    )


# Les corrigés sont chargés dans le Space « corriges », auquel le rôle
# « stagiaire » n'a pas accès. Les charger dans le Space de formation les
# afficherait au stagiaire dès sa première connexion, titres et descriptions
# compris — c'est-à-dire les réponses de M3 et M4, avant même de les chercher.
ESPACE = "corriges"


def main() -> int:
    espace = ESPACE
    dossier = conf.RACINE / "corriges"

    espace_formation = str(conf.valeur("formation.space_id"))

    identifiants = []
    for identifiant, fabrique in TABLEAUX.items():
        # Les premières versions chargeaient les corrigés dans le Space de
        # formation. Un lab existant les y porte encore, visibles du stagiaire
        # dès sa connexion — et Kibana refuse alors de recréer le même
        # identifiant ailleurs (HTTP 409, relevé en lab). On les retire.
        r = kbn("DELETE",
                f"/s/{espace_formation}/api/saved_objects/dashboard/{identifiant}")
        if r.status_code == 200:
            print(f"  [--] {identifiant} retiré du Space « {espace_formation} »")
        corps = fabrique()
        # Le JSON de l'API est un livrable à part entière : versionnable, relisible
        # en revue, rejouable sur la cible (SPEC §6.2, module M5).
        (dossier / f"{identifiant}.json").write_text(
            json.dumps(corps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        r = kbn("PUT", f"/s/{espace}/api/dashboards/{identifiant}", json=corps)
        if r.status_code not in (200, 201):
            raise SystemExit(
                f"API Dashboards a refusé « {corps['title']} » : "
                f"HTTP {r.status_code}\n{r.text[:900]}"
            )
        identifiants.append(identifiant)
        print(f"  [OK] {corps['title']:26s} {len(corps['panels'])} panneaux "
              f"(HTTP {r.status_code})")

    # Export ndjson : le second format exigé par P4. Il ne référence PAS la data
    # view par son identifiant — ces écrans, définis par l'API Dashboards, n'ont
    # aucune référence : leur motif d'index est écrit en ligne dans chaque
    # panneau, et c'est lui qu'on adapte pour la plateforme cible.
    export = kbn(
        "POST", f"/s/{espace}/api/saved_objects/_export",
        json={
            "objects": [{"type": "dashboard", "id": i} for i in identifiants],
            "includeReferencesDeep": True,
            "excludeExportDetails": False,
        },
    )
    if export.status_code != 200:
        raise SystemExit(f"export ndjson refusé : HTTP {export.status_code} {export.text[:400]}")
    cible = dossier / "tableaux-de-bord.ndjson"
    cible.write_bytes(export.content)
    lignes = export.content.decode("utf-8").strip().split("\n")
    print(f"  [OK] export ndjson : {len(lignes)} ligne(s), {len(export.content)} octets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
