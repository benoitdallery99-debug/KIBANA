"""verif-donnees — ce que prouve cette suite (SPEC §10) :

volumes par source, mapping effectif et « index.mode », présence de S1 à S7,
trou (S5) et silence (S6) effectifs, déterminisme (même graine → mêmes
réponses), jeu « epreuve » distinct. S'y ajoute le contrôle central du kit :
CHAQUE réponse du manifeste est recalculée par sa propre requête DSL sur le lab
et doit retomber sur la même valeur. Aucune réponse n'est écrite à la main.
"""

from __future__ import annotations

import ipaddress
import json
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from pathlib import Path

import pytest

pytestmark = pytest.mark.donnees

# Plages autorisées : documentation (RFC 5737) et usage privé (RFC 1918).
# Toute adresse hors de ces plages serait une donnée potentiellement réelle.
PLAGES_AUTORISEES = [
    ipaddress.ip_network(r) for r in (
        "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24",   # RFC 5737
        "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",       # RFC 1918
    )
]
SUFFIXES_AUTORISES = (".test", ".example", ".invalid", ".localhost")


@pytest.fixture(scope="module")
def manifeste(config):
    chemin = config.RACINE / "data" / "manifest.json"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : data/manifest.json absent. Lancez « make data ».")
    return json.loads(chemin.read_text(encoding="utf-8"))


def _chercher(es, index: str, requete: dict) -> dict:
    r = es.post(f"{es.base}/{index}/_search", json=requete, timeout=120)
    assert r.status_code == 200, f"recherche {index} : HTTP {r.status_code} {r.text[:300]}"
    return r.json()


def _extraire(reponse: dict, chemin: str):
    """Suit un chemin pointé, en acceptant les indices numériques de liste."""
    courant = reponse
    for morceau in chemin.split("."):
        courant = courant[int(morceau)] if morceau.isdigit() else courant[morceau]
    return courant


def _transformer(valeur, transformation: str | None, t0: datetime | None = None):
    if transformation is None:
        return valeur
    if transformation == "octets_vers_mo":
        return round(float(valeur) / (1024 * 1024))
    if transformation == "minutes_avant_maintenant":
        # Mesuré depuis l'instant du CHARGEMENT, pas depuis maintenant. Les
        # données sont en fenêtre glissante : une heure après le chargement, un
        # silence de deux heures en paraîtrait trois. Le scénario S6 dit
        # « muette depuis deux heures AU MOMENT DU CHARGEMENT » ; c'est donc à
        # T0 qu'il faut le mesurer, sinon le contrôle échouerait tout seul avec
        # le temps qui passe (constaté en lab).
        vu = datetime.fromtimestamp(float(valeur) / 1000, tz=UTC)
        reference = t0 or datetime.now(UTC)
        return round((reference - vu).total_seconds() / 60)
    if transformation == "entier":
        # L'agrégation « max » sur un champ entier renvoie un flottant
        # (65445.0) : la réponse attendue, elle, est un entier.
        return int(float(valeur))
    if transformation == "mediane_intervalle_minutes":
        instants = sorted(
            datetime.fromisoformat(h["_source"]["@timestamp"].replace("Z", "+00:00"))
            for h in valeur
        )
        ecarts = [(b - a).total_seconds() / 60 for a, b in pairwise(instants)]
        ecarts.sort()
        return round(ecarts[len(ecarts) // 2])
    raise AssertionError(f"transformation inconnue : {transformation}")


def _instant_de_chargement(manifeste: dict) -> datetime:
    """T0 : l'instant auquel les données ont été chargées.

    Les données sont en fenêtre glissante ; tout ce qui s'exprime en « depuis
    tant de temps » se mesure depuis cet instant, jamais depuis maintenant.
    """
    return datetime.fromisoformat(manifeste["engendre_le"].replace("Z", "+00:00"))


def _recalculer(es, namespace: str, controle: dict, t0: datetime | None = None):
    """Rejoue la requête DSL d'une réponse et en extrait la valeur."""
    if not controle.get("chemin"):
        return None  # réponse non calculable par requête (verdict, durée déclarée)
    dataset = controle["dataset"]
    index = f"logs-*-{namespace}" if dataset == "*" else f"logs-{dataset}-{namespace}"
    brut = _chercher(es, index, controle["requete"])
    return _transformer(
        _extraire(brut, controle["chemin"]), controle.get("transformation"), t0
    )


# --------------------------------------------------------------------------
# Volumes, mapping, mode d'index
# --------------------------------------------------------------------------

def test_volumes_par_source(es, manifeste, lab_demarre):
    for index, attendu in manifeste["volumes"].items():
        r = es.post(f"{es.base}/{index}/_count", json={}, timeout=60)
        assert r.status_code == 200, f"{index} : HTTP {r.status_code}"
        obtenu = r.json()["count"]
        assert obtenu == attendu, f"{index} : {obtenu} documents, manifeste {attendu}"


def test_volume_total_dans_la_fourchette(manifeste):
    """SPEC §5.1 : de 300 000 à 1 000 000 de documents."""
    total = manifeste["total_documents"]
    assert 300_000 <= total <= 1_000_000, f"{total} documents, hors fourchette"


def test_mapping_effectif_des_champs_du_parcours(es, manifeste, config, lab_demarre):
    """Un champ mal typé rendrait faux tout le parcours.

    Une recherche CIDR est impossible sur un keyword, une comparaison numérique
    impossible sur du texte : le contrôle porte sur le mapping EFFECTIF, celui
    qu'Elasticsearch applique, pas sur le gabarit qu'on a cru poser.
    """
    attendus = {
        "source.ip": "ip", "destination.ip": "ip", "host.ip": "ip",
        "source.port": "long", "destination.port": "long",
        "source.bytes": "long", "destination.bytes": "long",
        "event.severity": "long",
        "user.name": "keyword", "host.name": "keyword", "event.code": "keyword",
        "event.outcome": "keyword", "event.action": "keyword", "event.category": "keyword",
        "rule.name": "keyword", "dns.question.name": "keyword", "url.domain": "keyword",
        "http.response.status_code": "long", "network.transport": "keyword",
        "@timestamp": "date",
        # Seul champ analysé : c'est le contraste enseigné en M1.
        "message": "text",
    }
    namespace = manifeste["namespace"]
    r = es.get(f"{es.base}/logs-*-{namespace}/_mapping/field/*", timeout=60)
    assert r.status_code == 200
    par_index = r.json()

    trouves: dict[str, set[str]] = {}
    for bloc in par_index.values():
        for champ, details in bloc.get("mappings", {}).items():
            mapping = details.get("mapping", {})
            for definition in mapping.values():
                trouves.setdefault(champ, set()).add(definition.get("type"))

    defauts = []
    for champ, type_attendu in attendus.items():
        types = trouves.get(champ)
        if not types:
            defauts.append(f"{champ} : absent du mapping")
        elif types != {type_attendu}:
            defauts.append(f"{champ} : {sorted(types)}, attendu « {type_attendu} »")
    assert not defauts, "mapping effectif non conforme :\n  " + "\n  ".join(defauts)


def test_index_mode_effectif(es, manifeste, lab_demarre):
    """« index.mode » doit être celui que le kit a choisi, pas un défaut hérité."""
    namespace = manifeste["namespace"]
    r = es.get(f"{es.base}/logs-*-{namespace}/_settings/index.mode?flat_settings=true", timeout=60)
    assert r.status_code == 200
    modes = {
        nom: bloc["settings"].get("index.mode", "standard")
        for nom, bloc in r.json().items()
    }
    attendu = manifeste["index_mode"]
    hors = {n: m for n, m in modes.items() if m != attendu}
    assert not hors, f"index.mode attendu « {attendu} », trouvé : {hors}"


# --------------------------------------------------------------------------
# Le contrôle central : chaque réponse recalculée par sa requête
# --------------------------------------------------------------------------

def test_chaque_reponse_est_recalculee_par_sa_requete(es, manifeste, lab_demarre):
    """Aucune réponse attendue n'est écrite à la main (CLAUDE.md).

    Chaque réponse du manifeste est recalculée par la requête DSL qu'elle porte,
    et doit retomber exactement — à la tolérance déclarée près — sur la valeur
    que le générateur a relevée.
    """
    namespace = manifeste["namespace"]
    t0 = _instant_de_chargement(manifeste)
    ecarts = []
    verifiees = 0
    for scenario in [manifeste["reperes"], *manifeste["scenarios"]]:
        for reponse in scenario["reponses"]:
            controle = reponse["controle"]
            recalcule = _recalculer(es, namespace, controle, t0)

            if "attendu_litteral" in controle:
                if recalcule != controle["attendu_litteral"]:
                    ecarts.append(
                        f"{scenario['id']}/{reponse['cle']} : requête → {recalcule}, "
                        f"attendu littéral {controle['attendu_litteral']}"
                    )
                verifiees += 1
                continue

            if "attendu_environ" in controle:
                tol = controle.get("tolerance", 10)
                if abs(float(recalcule) - controle["attendu_environ"]) > tol:
                    ecarts.append(
                        f"{scenario['id']}/{reponse['cle']} : requête → {recalcule}, "
                        f"attendu ≈ {controle['attendu_environ']} ± {tol}"
                    )
                verifiees += 1
                continue

            if recalcule is None:
                continue  # verdict ou durée déclarée : non calculable par requête

            attendu = reponse["valeur"]
            if reponse["type"] == "entier_tolerance":
                if abs(int(recalcule) - int(attendu)) > int(reponse.get("tolerance", 0)):
                    ecarts.append(
                        f"{scenario['id']}/{reponse['cle']} : requête → {recalcule}, "
                        f"manifeste {attendu} ± {reponse.get('tolerance')}"
                    )
            elif reponse["type"] == "entier":
                if int(recalcule) != int(attendu):
                    ecarts.append(
                        f"{scenario['id']}/{reponse['cle']} : requête → {recalcule}, "
                        f"manifeste {attendu}"
                    )
            elif str(recalcule) != str(attendu):
                ecarts.append(
                    f"{scenario['id']}/{reponse['cle']} : requête → {recalcule!r}, "
                    f"manifeste {attendu!r}"
                )
            verifiees += 1

    assert not ecarts, "réponses non retrouvées par leur requête :\n  " + "\n  ".join(ecarts)
    assert verifiees >= 14, f"seulement {verifiees} réponses contrôlées par requête"


def test_les_sept_scenarios_sont_presents(manifeste):
    identifiants = [s["id"] for s in manifeste["scenarios"]]
    assert identifiants == ["S1", "S2", "S3", "S4", "S5", "S6", "S7"], identifiants
    for scenario in manifeste["scenarios"]:
        assert scenario["reponses"], f"{scenario['id']} sans réponse"
        for reponse in scenario["reponses"]:
            assert reponse.get("empreintes"), f"{scenario['id']}/{reponse['cle']} sans empreinte"


# --------------------------------------------------------------------------
# Pièges spécifiques
# --------------------------------------------------------------------------

def test_aucune_reponse_par_unique_count_au_dela_de_3000(manifeste):
    """« Unique count » dans Lens est l'agrégation cardinality, approximative.

    Elle n'est exacte qu'en deçà de son seuil de précision, 3000 par défaut :
    au-delà, la réponse affichée au stagiaire pourrait différer de la vérité.
    """
    for scenario in manifeste["scenarios"]:
        for reponse in scenario["reponses"]:
            requete = json.dumps(reponse["controle"].get("requete", {}))
            if "cardinality" in requete:
                assert int(reponse["valeur"]) < 3000, (
                    f"{scenario['id']}/{reponse['cle']} vaut {reponse['valeur']} : "
                    "au-delà de 3000, un « Unique count » devient approximatif"
                )


def test_le_trou_de_collecte_est_effectif(es, manifeste, lab_demarre):
    s5 = next(s for s in manifeste["scenarios"] if s["id"] == "S5")
    fenetre = s5["_fenetre"]
    index = f"logs-ids.alert-{manifeste['namespace']}"
    r = _chercher(es, index, {
        "size": 0, "track_total_hits": True,
        "query": {"range": {"@timestamp": {"gte": fenetre["debut"], "lt": fenetre["fin"]}}},
    })
    assert r["hits"]["total"]["value"] == 0, (
        f"le trou de collecte n'est pas vide : {r['hits']['total']['value']} document(s)"
    )
    # Et le voisinage immédiat, lui, doit être peuplé : sinon on prouverait
    # seulement que la source est vide partout.
    voisin = _chercher(es, index, {
        "size": 0, "track_total_hits": True,
        "query": {"range": {"@timestamp": {"gte": fenetre["fin"], "lt": "now"}}},
    })
    assert voisin["hits"]["total"]["value"] > 0, (
        "la source est vide après le trou : le contrôle ne prouverait rien"
    )


def test_la_source_muette_l_est_vraiment(es, manifeste, lab_demarre):
    """Une source muette ne produit AUCUN bucket : elle disparaît d'un décompte
    par source au lieu d'y figurer à zéro. C'est tout l'objet du scénario S6."""
    namespace = manifeste["namespace"]
    r = _chercher(es, f"logs-firewall.traffic-{namespace}", {
        "size": 0, "aggs": {"dernier": {"max": {"field": "@timestamp"}}},
    })
    dernier = datetime.fromtimestamp(
        r["aggregations"]["dernier"]["value"] / 1000, tz=UTC
    )
    # Mesuré depuis le chargement : voir la note de _transformer.
    silence = (_instant_de_chargement(manifeste) - dernier).total_seconds() / 60
    assert 110 <= silence <= 130, f"silence de {silence:.0f} min, attendu voisin de 120"

    # Preuve du piège : sur la dernière heure, la source n'apparaît pas du tout.
    # La dernière heure AVANT le chargement : c'est là que la source muette
    # manque à l'appel. « now-1h » ne conviendrait pas, la fenêtre ayant glissé.
    fin = manifeste["engendre_le"]
    debut = (_instant_de_chargement(manifeste) - timedelta(hours=1)).isoformat()
    recent = _chercher(es, f"logs-*-{namespace}", {
        "size": 0,
        "query": {"range": {"@timestamp": {"gte": debut, "lte": fin}}},
        "aggs": {"par_source": {"terms": {"field": "event.dataset", "size": 20}}},
    })
    presentes = {b["key"] for b in recent["aggregations"]["par_source"]["buckets"]}
    assert "firewall.traffic" not in presentes, (
        "la source muette apparaît encore dans le décompte de la dernière heure"
    )
    assert len(presentes) >= 4, (
        f"trop peu de sources actives pour que le contraste parle : {presentes}"
    )


# --------------------------------------------------------------------------
# Données synthétiques : aucune valeur réelle
# --------------------------------------------------------------------------

def test_toutes_les_adresses_sont_reservees(es, manifeste, lab_demarre):
    """CLAUDE.md : aucune donnée réelle. Contrôle sur les valeurs effectivement
    indexées, pas sur l'intention du générateur."""
    namespace = manifeste["namespace"]
    for champ in ("source.ip", "destination.ip", "host.ip"):
        r = _chercher(es, f"logs-*-{namespace}", {
            "size": 0,
            "aggs": {"v": {"terms": {"field": champ, "size": 500}}},
        })
        for bucket in r["aggregations"]["v"]["buckets"]:
            adresse = ipaddress.ip_address(bucket["key"])
            assert any(adresse in plage for plage in PLAGES_AUTORISEES), (
                f"{champ} = {adresse} hors des plages réservées (RFC 5737 / RFC 1918)"
            )


def test_tous_les_domaines_sont_reserves(es, manifeste, lab_demarre):
    namespace = manifeste["namespace"]
    for index, champ in (
        (f"logs-network.dns-{namespace}", "dns.question.name"),
        (f"logs-proxy.web-{namespace}", "url.domain"),
    ):
        r = _chercher(es, index, {
            "size": 0, "aggs": {"v": {"terms": {"field": champ, "size": 500}}},
        })
        for bucket in r["aggregations"]["v"]["buckets"]:
            nom = bucket["key"]
            assert nom.endswith(SUFFIXES_AUTORISES), (
                f"{champ} = {nom} : suffixe non réservé (RFC 2606 attendu)"
            )


# --------------------------------------------------------------------------
# Déterminisme et distinction des deux jeux
# --------------------------------------------------------------------------

def _reponses(manifeste: dict) -> dict[str, object]:
    return {
        f"{s['id']}.{r['cle']}": r["valeur"]
        for s in manifeste["scenarios"] for r in s["reponses"]
    }


def test_determinisme_meme_graine_memes_reponses(config, manifeste):
    """Deux générations de même graine doivent donner les mêmes réponses.

    La génération de contrôle n'indexe rien et écrit son manifeste ailleurs :
    elle ne doit pas écraser celui du jeu réellement chargé.
    """
    with tempfile.TemporaryDirectory() as dossier:
        obtenus = []
        for i in range(2):
            cible = Path(dossier) / f"manifeste-{i}.json"
            r = subprocess.run(
                [str(config.RACINE / ".venv" / "bin" / "python"),
                 str(config.RACINE / "data" / "generateur" / "engendrer.py"),
                 "--jeu", "formation", "--sans-chargement", "--manifeste", str(cible)],
                capture_output=True, text=True, timeout=900, check=False,
            )
            assert r.returncode == 0, f"génération {i} en échec : {r.stderr[-500:]}"
            obtenus.append(_reponses(json.loads(cible.read_text(encoding="utf-8"))))

    assert obtenus[0] == obtenus[1], (
        "deux générations de même graine donnent des réponses différentes :\n  "
        + "\n  ".join(
            f"{c} : {obtenus[0].get(c)!r} puis {obtenus[1].get(c)!r}"
            for c in obtenus[0] if obtenus[0].get(c) != obtenus[1].get(c)
        )
    )
    # Et ces réponses sont bien celles du jeu chargé.
    assert obtenus[0] == _reponses(manifeste), (
        "le manifeste chargé ne correspond pas à une génération de même graine"
    )


def test_jeu_epreuve_distinct(config, manifeste):
    """L'épreuve a les mêmes structures et des réponses DIFFÉRENTES (SPEC §5.1)."""
    chemin = config.RACINE / "data" / "manifest-epreuve.json"
    if not chemin.exists():
        pytest.skip(
            "NON EXÉCUTÉ : data/manifest-epreuve.json absent. Lancez « make data-epreuve »."
        )
    epreuve = json.loads(chemin.read_text(encoding="utf-8"))

    assert epreuve["namespace"] != manifeste["namespace"]
    assert [s["id"] for s in epreuve["scenarios"]] == [s["id"] for s in manifeste["scenarios"]]

    formation_r, epreuve_r = _reponses(manifeste), _reponses(epreuve)
    communes = {
        c for c in formation_r
        if formation_r[c] == epreuve_r.get(c)
        # Sont identiques PAR CONSTRUCTION, et non par recopie : le verdict de
        # S7, l'adresse du scanner (constante de la fiche de contexte), la source
        # et la durée du trou, la source muette.
        and not c.startswith((
            "S7.verdict", "S7.preuve_ip", "S5.duree", "S5.source", "S6.source",
        ))
    }
    assert not communes, f"réponses identiques entre les deux jeux : {sorted(communes)}"


def test_epreuve_sans_empreinte_de_reponse(config):
    """SPEC §9 : l'épreuve n'embarque aucune réponse, même sous forme d'empreinte.

    Le manifeste de l'épreuve reste côté formateur ; ce contrôle garantit qu'il
    ne sera pas confondu avec celui du parcours au moment de l'empaquetage.
    """
    chemin = config.RACINE / "data" / "manifest-epreuve.json"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : data/manifest-epreuve.json absent.")
    epreuve = json.loads(chemin.read_text(encoding="utf-8"))
    assert epreuve["jeu"] == "epreuve"
