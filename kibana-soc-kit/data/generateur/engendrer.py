"""Engendre et charge le jeu de données synthétiques — SPEC §5.

    .venv/bin/python data/generateur/engendrer.py --jeu formation
    .venv/bin/python data/generateur/engendrer.py --jeu epreuve

Écrit data/manifest.json : pour chaque scénario, les réponses RELEVÉES sur les
données produites, leur type, leur règle de normalisation, leur requête DSL de
contrôle, et les empreintes SHA-256 des réponses normalisées — seules ces
empreintes seront embarquées dans le guide.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

RACINE_GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE_GEN))
sys.path.insert(0, str(RACINE_GEN.parent.parent))

import contexte as ctx  # noqa: E402
import evenements as E  # noqa: E402
import gabarits as G  # noqa: E402
import scenarios as SC  # noqa: E402
import temps as T  # noqa: E402

from outils import conf  # noqa: E402

# Volumes du bruit de fond, par source. Total voisin de 385 000 documents,
# dans la fourchette de SPEC §5.1 (300 000 à 1 000 000).
VOLUMES = {
    "windows.security": 90_000,
    "linux.auth": 35_000,
    "ids.alert": 15_000,
    "network.dns": 100_000,
    "proxy.web": 75_000,
    "firewall.traffic": 70_000,
}

TAILLE_LOT = 5_000


# --- Normalisation et empreintes --------------------------------------------

def normaliser(valeur, regle: str) -> str:
    """Applique la règle de normalisation déclarée dans le manifeste.

    La même fonction est reproduite en JavaScript dans le guide : c'est elle qui
    permet de valider la réponse d'un stagiaire sans jamais embarquer la réponse.
    """
    texte = str(valeur).strip()
    if "minuscules" in regle:
        texte = texte.lower()
    if "accents retirés" in regle:
        texte = "".join(
            c for c in unicodedata.normalize("NFD", texte)
            if unicodedata.category(c) != "Mn"
        )
    if "espaces retirés" in regle:
        texte = " ".join(texte.split())
    return texte


def empreintes(reponse: dict) -> list[str]:
    """Empreintes acceptées pour une réponse.

    Pour une réponse tolérante (« entier ± tolérance »), toutes les valeurs de
    l'intervalle ont leur empreinte : le guide accepte donc un ordre de grandeur
    juste sans jamais détenir la valeur exacte.
    """
    regle = reponse.get("normalisation", "espaces retirés")
    valeurs = [reponse["valeur"]]
    if reponse.get("type") == "entier_tolerance":
        tol = int(reponse.get("tolerance", 0))
        centre = int(reponse["valeur"])
        valeurs = list(range(centre - tol, centre + tol + 1))
    return [
        hashlib.sha256(normaliser(v, regle).encode("utf-8")).hexdigest()
        for v in valeurs
    ]


# --- Dialogue avec Elasticsearch --------------------------------------------

def es(methode: str, chemin: str, **kw):
    return requests.request(
        methode, f"{conf.url_es()}{chemin}",
        auth=conf.auth_elastic(),
        headers={"Content-Type": "application/json"},
        timeout=180, **kw,
    )


def poser_gabarits(namespace: str) -> None:
    for nom, corps in G.tous_les_gabarits(namespace).items():
        r = es("PUT", f"/_index_template/{nom}", json=corps)
        if r.status_code not in (200, 201):
            raise SystemExit(f"gabarit {nom} refusé : HTTP {r.status_code} {r.text[:400]}")
    print(f"  gabarits posés : {len(G.DATASETS)} "
          f"(priorité {G.PRIORITE}, index.mode {G.MODE_INDEX})")


def purger(namespace: str) -> None:
    """Supprime les data streams du namespace : le chargement repart à neuf."""
    r = es("DELETE", f"/_data_stream/logs-*-{namespace}")
    if r.status_code not in (200, 404):
        print(f"  (purge : HTTP {r.status_code} {r.text[:200]})")
    else:
        print(f"  data streams logs-*-{namespace} purgés")


def indexer(dataset: str, namespace: str, documents: list[dict]) -> int:
    """Indexation par _bulk. L'action « create » est la seule acceptée par un
    data stream : un « index » serait refusé."""
    flux = G.nom_data_stream(dataset, namespace)
    envoyes = 0
    for depart in range(0, len(documents), TAILLE_LOT):
        lot = documents[depart:depart + TAILLE_LOT]
        corps = "".join(
            '{"create":{}}\n' + json.dumps(d, ensure_ascii=False) + "\n" for d in lot
        )
        r = requests.post(
            f"{conf.url_es()}/{flux}/_bulk",
            auth=conf.auth_elastic(),
            headers={"Content-Type": "application/x-ndjson"},
            data=corps.encode("utf-8"),
            timeout=300,
        )
        if r.status_code >= 300:
            raise SystemExit(f"_bulk {flux} : HTTP {r.status_code} {r.text[:500]}")
        reponse = r.json()
        if reponse.get("errors"):
            premier = next(
                (i["create"] for i in reponse["items"] if i["create"].get("error")), None
            )
            raise SystemExit(f"_bulk {flux} a refusé des documents : {json.dumps(premier)[:600]}")
        envoyes += len(lot)
    return envoyes


# --- Application des scénarios ----------------------------------------------

def appliquer_retraits(base: dict[str, list[dict]], retraits: list) -> dict[str, list[dict]]:
    """Retire du bruit de fond ce que les scénarios exigent d'en retirer :
    trou de collecte, source muette, adresse réservée à un scénario."""
    for dataset, critere in retraits:
        avant = len(base.get(dataset, []))
        if "_intervalle" in critere:
            debut, fin = critere["_intervalle"]
            debut_iso, fin_iso = T.iso(debut), T.iso(fin)
            base[dataset] = [
                d for d in base[dataset] if not (debut_iso <= d["@timestamp"] < fin_iso)
            ]
        else:
            # Critère par champs : un événement n'est retiré que s'il correspond
            # à TOUS les champs donnés.
            def correspond(d: dict, critere: dict = critere) -> bool:
                for chemin, attendu in critere.items():
                    racine, feuille = chemin.split(".", 1)
                    if d.get(racine, {}).get(feuille) != attendu:
                        return False
                return True

            base[dataset] = [d for d in base[dataset] if not correspond(d)]
        print(f"  retrait sur {dataset} : {avant - len(base[dataset])} événement(s)")
    return base


def reperes(base: dict[str, list[dict]]) -> dict:
    """Repères : des réponses vraies, stables et vérifiables, qui ne dévoilent
    aucun scénario.

    Les modules M0 à M3 enseignent des gestes ; leurs exercices ont donc besoin
    de réponses contrôlables sans entamer l'enquête des modules M4. Ces repères
    sont, eux aussi, RELEVÉS sur les données produites et recalculables par une
    requête — jamais écrits à la main.
    """
    par_dataset = {d: len(v) for d, v in base.items()}
    plus_volumineuse = max(par_dataset, key=lambda d: par_dataset[d])

    hotes = {
        d.get("host", {}).get("name")
        for evenements in base.values() for d in evenements
        if d.get("host", {}).get("name")
    }

    par_hote: dict[str, int] = {}
    for evenements in base.values():
        for d in evenements:
            nom = d.get("host", {}).get("name")
            if nom:
                par_hote[nom] = par_hote.get(nom, 0) + 1
    hote_actif = max(par_hote, key=lambda h: par_hote[h]) if par_hote else ""

    # --- Faits supplémentaires, un par exercice -----------------------------
    # Trente exercices se partageaient treize réponses : un stagiaire pouvait
    # retaper de mémoire une valeur relevée trois modules plus tôt, sans avoir
    # refait le geste. Chaque fait ci-dessous est relevé sur les données
    # engendrées et recalculable par une requête, comme tous les autres.
    moins_volumineuse = min(par_dataset, key=lambda d: par_dataset[d])

    # Les comptes vus dans les journaux d'authentification. Le vivier de comptes
    # est fixe, et sur plus de cent mille événements ils apparaissent tous :
    # le nombre ne bouge donc pas d'une génération à l'autre. Il n'est publié
    # nulle part — la fiche de contexte ne nomme que les comptes de service et
    # les comptes d'administration —, et il se relève en filtrant sur les deux
    # sources d'authentification, ce qui est exactement le geste de l'exercice.
    # Combien de sources portent un nom de compte. Fait de structure, stable,
    # et surtout OBTENABLE avec ce que le module M1 enseigne : une requête par
    # valeur, et on lit le compteur. Le nombre de comptes distincts, lui,
    # exigeait un décompte de valeurs distinctes que M1 n'a pas encore donné.
    sources_avec_compte = {
        dataset for dataset, evenements in base.items()
        if any(d.get("user", {}).get("name") for d in evenements)
    }

    comptes_auth = {
        d.get("user", {}).get("name")
        for dataset in ("windows.security", "linux.auth")
        for d in base.get(dataset, [])
        if d.get("user", {}).get("name")
    }

    ports = [
        d["destination"]["port"]
        for evenements in base.values() for d in evenements
        if isinstance(d.get("destination"), dict) and d["destination"].get("port")
    ]
    port_max = max(ports) if ports else 0

    # Quelle source porte les connexions vers les ports hauts — un CLASSEMENT,
    # et non un décompte. Le pare-feu en produit six fois plus que la sonde, et
    # cet écart-là ne bouge pas ; le nombre de documents, lui, varie de quelques
    # unités selon l'endroit où la fenêtre glissante tombe dans la semaine.
    ports_hauts: dict[str, int] = {}
    for dataset, evenements in base.items():
        for d in evenements:
            dst = d.get("destination")
            if isinstance(dst, dict) and (dst.get("port") or 0) >= 1025:
                ports_hauts[dataset] = ports_hauts.get(dataset, 0) + 1
    source_ports_hauts = (
        max(ports_hauts, key=lambda s: ports_hauts[s]) if ports_hauts else ""
    )

    # Heure ouvrée la plus chargée, dans le fuseau métier : c'est ce que montre
    # un croisement sources × heures, et Kibana affiche dans le fuseau du
    # navigateur — d'où la conversion explicite.
    fuseau = ZoneInfo(str(conf.valeur("donnees.fuseau_metier")))
    par_heure: dict[int, int] = {}
    for evenements in base.values():
        for d in evenements:
            heure = datetime.fromisoformat(
                d["@timestamp"].replace("Z", "+00:00")
            ).astimezone(fuseau).hour
            par_heure[heure] = par_heure.get(heure, 0) + 1
    heure_chargee = max(par_heure, key=lambda h: par_heure[h]) if par_heure else 0

    signatures: dict[str, int] = {}
    for evenement in base.get("ids.alert", []):
        nom = evenement["rule"]["name"]
        signatures[nom] = signatures.get(nom, 0) + 1
    signature_frequente = max(signatures, key=lambda s: signatures[s]) if signatures else ""

    return {
        "id": "R",
        "titre": "Repères du jeu de données",
        "recit": (
            "Des faits vrais, stables et vérifiables sur le jeu de données, qui servent de "
            "réponses aux exercices de prise en main sans rien dévoiler des scénarios."
        ),
        "reponses": [
            {
                "cle": "nb_sources", "libelle": "Nombre de sources qui alimentent la data view",
                "valeur": len(base), "type": "entier", "normalisation": "entier",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0, "aggs": {"r": {"cardinality": {
                        "field": "event.dataset", "precision_threshold": 40000}}}},
                    "chemin": "aggregations.r.value",
                },
            },
            {
                "cle": "source_la_plus_volumineuse",
                "libelle": "Source qui produit le plus d'événements",
                "valeur": plus_volumineuse, "type": "texte",
                "normalisation": "minuscules, espaces retirés",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0, "aggs": {"r": {"terms": {
                        "field": "event.dataset", "size": 1}}}},
                    "chemin": "aggregations.r.buckets.0.key",
                },
            },
            {
                # Lisible dès M0 dans la barre latérale de Discover : le pare-feu
                # y sort à 20 %, les postes autour de 6 %. L'écart est assez large
                # pour survivre à l'échantillonnage du panneau de champ — ce que
                # le contrôle ci-dessous confirme sur la TOTALITÉ des documents.
                "cle": "hote_le_plus_actif",
                "libelle": "Machine qui produit le plus d'événements",
                "valeur": hote_actif, "type": "texte",
                "normalisation": "minuscules, espaces retirés",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0, "aggs": {"r": {"terms": {
                        "field": "host.name", "size": 1}}}},
                    "chemin": "aggregations.r.buckets.0.key",
                },
            },
            {
                "cle": "nb_hotes", "libelle": "Nombre d'hôtes distincts observés",
                "valeur": len(hotes), "type": "entier", "normalisation": "entier",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0, "aggs": {"r": {"cardinality": {
                        "field": "host.name", "precision_threshold": 40000}}}},
                    "chemin": "aggregations.r.value",
                },
            },
            {
                "cle": "source_la_moins_volumineuse",
                "libelle": "Source qui produit le moins d'événements",
                "valeur": moins_volumineuse, "type": "texte",
                "normalisation": "minuscules, espaces retirés",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0, "aggs": {"r": {"terms": {
                        "field": "event.dataset", "size": 1,
                        "order": {"_count": "asc"}}}}},
                    "chemin": "aggregations.r.buckets.0.key",
                },
            },
            {
                "cle": "nb_sources_avec_compte",
                "libelle": "Sources qui renseignent un nom de compte",
                "valeur": len(sources_avec_compte), "type": "entier",
                "normalisation": "entier",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0,
                                "query": {"exists": {"field": "user.name"}},
                                "aggs": {"r": {"cardinality": {
                                    "field": "event.dataset",
                                    "precision_threshold": 40000}}}},
                    "chemin": "aggregations.r.value",
                },
            },
            {
                "cle": "nb_comptes_authentification",
                "libelle": "Comptes distincts vus dans les journaux d'authentification",
                "valeur": len(comptes_auth), "type": "entier",
                "normalisation": "entier",
                "controle": {
                    "dataset": "*",
                    "requete": {
                        "size": 0,
                        "query": {"terms": {"event.dataset": [
                            "windows.security", "linux.auth"]}},
                        "aggs": {"r": {"cardinality": {
                            "field": "user.name", "precision_threshold": 40000}}},
                    },
                    "chemin": "aggregations.r.value",
                },
            },
            {
                "cle": "source_ports_hauts",
                "libelle": "Source qui produit le plus de connexions vers un port de 1025 ou plus",
                "valeur": source_ports_hauts, "type": "texte",
                "normalisation": "minuscules, espaces retirés",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0,
                                "query": {"range": {"destination.port": {"gte": 1025}}},
                                "aggs": {"r": {"terms": {
                                    "field": "event.dataset", "size": 1}}}},
                    "chemin": "aggregations.r.buckets.0.key",
                },
            },
            {
                "cle": "port_destination_max",
                "libelle": "Port de destination le plus élevé observé",
                "valeur": port_max, "type": "entier", "normalisation": "entier",
                "controle": {
                    "dataset": "*",
                    "requete": {"size": 0, "aggs": {"r": {"max": {
                        "field": "destination.port"}}}},
                    "chemin": "aggregations.r.value",
                    "transformation": "entier",
                },
            },
            {
                "cle": "heure_la_plus_chargee",
                "libelle": "Heure du jour la plus chargée, dans le fuseau métier",
                "valeur": heure_chargee, "type": "entier", "normalisation": "entier",
                "controle": {
                    "dataset": "*",
                    # Le champ « heure » n'existe pas à l'indexation : il est
                    # calculé au vol. C'est la seule façon d'obtenir une heure
                    # du jour — et non un instant — sans toucher au mapping.
                    "requete": {
                        "size": 0,
                        "runtime_mappings": {"heure": {"type": "long", "script": {
                            "source": "emit(doc['@timestamp'].value"
                                      ".withZoneSameInstant(ZoneId.of(params.fuseau))"
                                      ".getHour())",
                            "params": {"fuseau": str(conf.valeur("donnees.fuseau_metier"))},
                        }}},
                        "aggs": {"r": {"terms": {"field": "heure", "size": 1}}},
                    },
                    "chemin": "aggregations.r.buckets.0.key",
                },
            },
            {
                "cle": "nb_signatures_distinctes",
                "libelle": "Signatures distinctes levées par la sonde",
                "valeur": len(signatures), "type": "entier", "normalisation": "entier",
                "controle": {
                    "dataset": "ids.alert",
                    "requete": {"size": 0, "aggs": {"r": {"cardinality": {
                        "field": "rule.name", "precision_threshold": 40000}}}},
                    "chemin": "aggregations.r.value",
                },
            },
            {
                "cle": "signature_ids_la_plus_frequente",
                "libelle": "Signature IDS la plus fréquente",
                "valeur": signature_frequente, "type": "texte",
                "normalisation": "minuscules, espaces retirés",
                "controle": {
                    "dataset": "ids.alert",
                    "requete": {"size": 0, "aggs": {"r": {"terms": {
                        "field": "rule.name", "size": 1}}}},
                    "chemin": "aggregations.r.buckets.0.key",
                },
            },
        ],
    }


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--jeu", choices=["formation", "epreuve"], default="formation")
    a.add_argument("--sans-chargement", action="store_true",
                   help="engendre et écrit le manifeste sans indexer (mise au point)")
    a.add_argument("--manifeste", default=None,
                   help="chemin du manifeste à écrire (défaut : data/manifest.json). "
                        "Sert au contrôle de déterminisme, qui ne doit pas écraser "
                        "le manifeste du jeu réellement chargé.")
    args = a.parse_args()

    prefixe = "donnees" if args.jeu == "formation" else "epreuve"
    graine = int(conf.valeur(f"{prefixe}.graine"))
    namespace = str(conf.valeur(f"{prefixe}.namespace"))
    jours = int(conf.valeur("donnees.fenetre_jours"))
    fuseau = str(conf.valeur("donnees.fuseau_metier"))

    t0 = T.maintenant()
    print(f"Jeu « {args.jeu} » — graine {graine}, namespace {namespace}, "
          f"fenêtre {jours} j se terminant à {T.iso(t0)}")

    # Deux générateurs distincts : le bruit de fond d'un côté, les scénarios de
    # l'autre. Les réponses ne dépendent ainsi pas du volume de bruit.
    rng_bruit = random.Random(graine)
    rng_scenarios = random.Random(graine + 1)

    print("Bruit de fond :")
    base: dict[str, list[dict]] = {}
    for dataset, combien in VOLUMES.items():
        instants = T.horodatages(rng_bruit, combien, t0, jours, fuseau)
        base[dataset] = E.GENERATEURS[dataset](rng_bruit, instants)
        print(f"  {dataset:20s} {len(base[dataset]):7d}")

    print("Scénarios :")
    manifeste_scenarios = []
    for fabrique in SC.TOUS:
        resultat = fabrique(rng_scenarios, t0, jours, fuseau)
        appliquer_retraits(base, resultat["retraits"])
        for dataset, evenements in resultat["ajouts"].items():
            base.setdefault(dataset, []).extend(evenements)
        m = resultat["manifeste"]
        for reponse in m["reponses"]:
            reponse["empreintes"] = empreintes(reponse)
        manifeste_scenarios.append(m)
        ajoutes = sum(len(v) for v in resultat["ajouts"].values())
        print(f"  {m['id']} {m['titre'][:52]:52s} +{ajoutes}")

    # Les scénarios ne sont plus appliqués dans l'ordre de leurs identifiants —
    # celui qui creuse un trou doit passer après celui qui dépose des événements
    # dans la même source. Le manifeste, lui, se lit : on le remet dans l'ordre.
    manifeste_scenarios.sort(key=lambda m: m["id"])

    for dataset in base:
        base[dataset].sort(key=lambda d: d["@timestamp"])
    total = sum(len(v) for v in base.values())
    print(f"Total : {total} documents")

    if not args.sans_chargement:
        print("Chargement :")
        poser_gabarits(namespace)
        purger(namespace)
        for dataset, documents in base.items():
            envoyes = indexer(dataset, namespace, documents)
            print(f"  {G.nom_data_stream(dataset, namespace):34s} {envoyes:7d}")
        es("POST", f"/logs-*-{namespace}/_refresh")

    reperes_calcules = reperes(base)
    for reponse in reperes_calcules["reponses"]:
        reponse["empreintes"] = empreintes(reponse)

    manifeste = {
        "engendre_le": T.iso(t0),
        "jeu": args.jeu,
        "graine": graine,
        "namespace": namespace,
        "fenetre_jours": jours,
        "fuseau_metier": fuseau,
        "version_stack": conf.version(),
        "index_mode": G.MODE_INDEX,
        "avertissement": (
            "Données entièrement synthétiques. Adresses réservées à la documentation "
            "(RFC 5737, RFC 1918), domaines réservés (RFC 2606), personnes inventées. "
            "Aucune donnée réelle (SPEC §5.1, CLAUDE.md)."
        ),
        "volumes": {G.nom_data_stream(d, namespace): len(v) for d, v in base.items()},
        "total_documents": total,
        "contexte": ctx.fiche_contexte(),
        "reperes": reperes_calcules,
        "scenarios": manifeste_scenarios,
    }
    sortie = Path(args.manifeste) if args.manifeste else conf.RACINE / "data" / (
        "manifest.json" if args.jeu == "formation" else "manifest-epreuve.json"
    )
    sortie.write_text(
        json.dumps(manifeste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    try:
        affiche = sortie.relative_to(conf.RACINE)
    except ValueError:
        affiche = sortie
    print(f"Manifeste écrit : {affiche}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
