"""Les sept scénarios cachés — SPEC §5.3.

Chaque scénario renvoie :
- « ajouts »    : les événements à insérer, par dataset ;
- « retraits »  : un filtre à appliquer au bruit de fond (trou de collecte,
                  source muette, exclusion d'une adresse) ;
- « manifeste » : les réponses attendues, RELEVÉES sur les données produites,
                  chacune accompagnée de sa requête DSL de contrôle.

Les scénarios tirent dans un générateur aléatoire DISTINCT de celui du bruit de
fond : les réponses restent ainsi identiques d'une exécution à l'autre, même si
le volume de bruit change. C'est ce qui rend le déterminisme vérifiable.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import contexte as ctx
import temps as T
from evenements import _fusion, _socle


def _nuit_du_milieu(
    t0: datetime, jours: int, fuseau: str, recul_jours: int, heure: int
) -> datetime:
    """Un instant situé à « recul_jours » avant T0, à l'heure locale voulue.

    L'heure est fixée dans le fuseau métier — un scénario nocturne doit tomber
    la nuit pour l'analyste, pas la nuit UTC — puis reconvertie en UTC.
    """
    cible = (t0 - timedelta(days=recul_jours)).astimezone(ZoneInfo(fuseau))
    cible = cible.replace(hour=heure, minute=0, second=0, microsecond=0)
    return cible.astimezone(UTC)


# ---------------------------------------------------------------------------
# S1 — Force brute externe, puis succès sur un compte de service
# ---------------------------------------------------------------------------

def s1_force_brute(rng: random.Random, t0: datetime, jours: int, fuseau: str) -> dict:
    ip = f"198.51.100.{rng.randrange(20, 240)}"
    compte = rng.choice(ctx.COMPTES_DE_SERVICE)["nom"]
    # L'hôte visé est tiré : sans cela, il serait identique dans le jeu du
    # parcours et dans celui de l'épreuve, et la réponse se recopierait.
    cible = rng.choice([
        h for h in ctx.TOUS_LES_HOTES
        if h["os"] == "windows" and h["critique"] and not h.get("equipement")
    ])
    echecs = rng.randrange(38, 73)

    depart = _nuit_du_milieu(t0, jours, fuseau, recul_jours=3, heure=2)
    evenements = []
    instant = depart
    for i in range(echecs):
        instant = depart + timedelta(seconds=int(i * rng.uniform(18, 34)))
        evenements.append(_fusion(_socle(instant, "windows.security"), {
            "event": {
                "kind": "event", "category": ["authentication"], "type": ["start"],
                "action": "ouverture-de-session", "code": "4625", "outcome": "failure",
            },
            "user": {"name": compte, "domain": ctx.DOMAINE_AD},
            "host": {"name": cible["nom"], "ip": cible["ip"], "os": {"type": "windows"}},
            "source": {"ip": ip},
            "winlog": {"channel": "Security", "logon": {"type": "3"}},
            "message": f"Echec d'ouverture de session pour {compte} depuis {ip}",
        }))
    # Le succès arrive APRÈS tous les échecs : la réponse « nombre d'échecs avant
    # le succès » est donc exactement le nombre d'échecs de ce couple compte/IP,
    # ce qu'une simple requête sait compter.
    succes = instant + timedelta(seconds=rng.randrange(20, 50))
    evenements.append(_fusion(_socle(succes, "windows.security"), {
        "event": {
            "kind": "event", "category": ["authentication"], "type": ["start"],
            "action": "ouverture-de-session", "code": "4624", "outcome": "success",
        },
        "user": {"name": compte, "domain": ctx.DOMAINE_AD},
        "host": {"name": cible["nom"], "ip": cible["ip"], "os": {"type": "windows"}},
        "source": {"ip": ip},
        "winlog": {"channel": "Security", "logon": {"type": "3"}},
        "message": f"Ouverture de session reussie pour {compte} depuis {ip}",
    }))

    filtre_ip = {"term": {"source.ip": ip}}
    return {
        "ajouts": {"windows.security": evenements},
        "retraits": [],
        "manifeste": {
            "id": "S1",
            "titre": "Force brute externe suivie d'un succès sur un compte de service",
            "recit": (
                "Une adresse extérieure a tenté des dizaines d'ouvertures de session sur un "
                "compte de service, jusqu'à en réussir une."
            ),
            "reponses": [
                {
                    "cle": "source_ip", "libelle": "Adresse IP à l'origine des tentatives",
                    "valeur": ip, "type": "ip", "normalisation": "espaces retirés",
                    "controle": {
                        "dataset": "windows.security",
                        "requete": {"size": 0, "query": {"bool": {"filter": [
                            {"term": {"event.code": "4625"}}, {"term": {"user.name": compte}}]}},
                            "aggs": {"r": {"terms": {"field": "source.ip", "size": 1}}}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
                {
                    "cle": "compte", "libelle": "Compte visé", "valeur": compte,
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": "windows.security",
                        "requete": {"size": 0, "query": {"bool": {"filter": [
                            {"term": {"event.code": "4625"}}, filtre_ip]}},
                            "aggs": {"r": {"terms": {"field": "user.name", "size": 1}}}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
                {
                    "cle": "nb_echecs", "libelle": "Nombre d'échecs avant le succès",
                    "valeur": echecs, "type": "entier", "normalisation": "entier",
                    "controle": {
                        "dataset": "windows.security",
                        "requete": {"size": 0, "track_total_hits": True,
                                    "query": {"bool": {"filter": [
                                        {"term": {"event.code": "4625"}},
                                        {"term": {"user.name": compte}}, filtre_ip]}}},
                        "chemin": "hits.total.value",
                    },
                },
                {
                    "cle": "hote_cible", "libelle": "Hôte visé", "valeur": cible["nom"],
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": "windows.security",
                        "requete": {"size": 0, "query": {"bool": {"filter": [filtre_ip]}},
                                    "aggs": {"r": {"terms": {"field": "host.name", "size": 1}}}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# S2 — Balayage de ports interne
# ---------------------------------------------------------------------------

def s2_balayage(rng: random.Random, t0: datetime, jours: int, fuseau: str) -> dict:
    scanneur = rng.choice([p for p in ctx.POSTES if p["nom"].startswith("pc-tech")])
    cible = next(h for h in ctx.TOUS_LES_HOTES if h["nom"] == "srv-bdd-01")
    # Moins de 3000 ports distincts : au-delà, « Unique count » dans Lens
    # deviendrait approximatif et la réponse ne serait plus sûre (CLAUDE.md).
    nb_ports = rng.randrange(900, 1650)
    ports = rng.sample(range(1, 65535), nb_ports)

    depart = _nuit_du_milieu(t0, jours, fuseau, recul_jours=2, heure=23)
    evenements = []
    for i, port in enumerate(ports):
        instant = depart + timedelta(seconds=int(i * 600 / nb_ports))
        evenements.append(_fusion(_socle(instant, "firewall.traffic"), {
            "event": {"kind": "event", "category": ["network"], "type": ["connection"],
                      "action": "deny", "outcome": "failure"},
            "rule": {"id": "FW-020", "name": "Blocage par defaut"},
            "source": {"ip": scanneur["ip"], "port": rng.randrange(40000, 60000)},
            "destination": {"ip": cible["ip"], "port": port},
            "network": {"transport": "tcp", "direction": "internal"},
            "host": {"name": "fw-perimetre-01", "ip": "10.30.0.1"},
            "message": f"DENY {scanneur['ip']} -> {cible['ip']}:{port}",
        }))

    return {
        "ajouts": {"firewall.traffic": evenements},
        # Le bruit de fond est purgé du seul couple « ce poste → ce serveur » :
        # la réponse « nombre de ports distincts » est alors exactement celle du
        # balayage. Le poste conserve tout son trafic ordinaire vers le reste du
        # parc — le purger entièrement en ferait une machine muette, invraisemblable.
        "retraits": [("firewall.traffic", {
            "source.ip": scanneur["ip"], "destination.ip": cible["ip"],
        })],
        "manifeste": {
            "id": "S2",
            "titre": "Balayage de ports interne",
            "recit": (
                "Un poste interne a testé un grand nombre de ports sur un serveur, "
                "en dix minutes."
            ),
            "reponses": [
                {
                    "cle": "source_ip", "libelle": "Poste à l'origine du balayage",
                    "valeur": scanneur["ip"], "type": "ip", "normalisation": "espaces retirés",
                    "controle": {
                        "dataset": "firewall.traffic",
                        "requete": {"size": 0, "query": {"bool": {"filter": [
                            {"term": {"event.action": "deny"}},
                            {"term": {"destination.ip": cible["ip"]}}]}},
                            "aggs": {"r": {"terms": {"field": "source.ip", "size": 1}}}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
                {
                    "cle": "nb_ports", "libelle": "Nombre de ports distincts visés",
                    "valeur": nb_ports, "type": "entier", "normalisation": "entier",
                    "controle": {
                        "dataset": "firewall.traffic",
                        "requete": {"size": 0, "query": {"bool": {"filter": [
                            {"term": {"source.ip": scanneur["ip"]}},
                            {"term": {"destination.ip": cible["ip"]}}]}},
                            "aggs": {"r": {"cardinality": {
                                "field": "destination.port",
                                "precision_threshold": 40000,
                            }}}},
                        "chemin": "aggregations.r.value",
                    },
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# S3 — Balise périodique (beaconing) vers un domaine .test
# ---------------------------------------------------------------------------

def s3_balise(rng: random.Random, t0: datetime, jours: int, fuseau: str) -> dict:
    poste = rng.choice([p for p in ctx.POSTES if p["nom"].startswith("pc-compta")])
    domaine = f"maj-sys-{rng.randrange(100, 999)}.test"
    # Éventail large : avec quatre valeurs seulement, le parcours et l'épreuve
    # tombaient trop souvent sur la même période.
    periode = rng.choice([3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 17, 19, 23])  # minutes

    debut = T.debut_fenetre(t0, jours) + timedelta(hours=rng.randrange(3, 10))
    evenements = []
    instant = debut
    while instant < t0:
        # Gigue : ± 15 s autour d'une période fixe. Assez régulier pour être
        # reconnaissable, assez bruité pour ne pas être trivial.
        decale = instant + timedelta(seconds=rng.randint(-15, 15))
        if decale < t0:
            evenements.append(_fusion(_socle(decale, "network.dns"), {
                "event": {"kind": "event", "category": ["network"], "type": ["protocol"],
                          "action": "requete-dns", "outcome": "success"},
                "dns": {
                    "question": {"name": domaine, "type": "A",
                                 "registered_domain": domaine},
                    "response_code": "NOERROR",
                },
                "host": {"name": poste["nom"], "ip": poste["ip"]},
                "source": {"ip": poste["ip"]},
                "destination": {"ip": "10.20.1.10", "port": 53},
                "network": {"transport": "udp", "protocol": "dns"},
                "message": f"Requete DNS {domaine} depuis {poste['ip']}",
            }))
        instant += timedelta(minutes=periode)

    return {
        "ajouts": {"network.dns": evenements},
        "retraits": [],
        "manifeste": {
            "id": "S3",
            "titre": "Balise périodique vers un domaine externe",
            "recit": (
                "Un poste interroge le même domaine à intervalle régulier, jour et nuit, "
                "week-end compris."
            ),
            "reponses": [
                {
                    "cle": "hote", "libelle": "Poste émetteur", "valeur": poste["nom"],
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": "network.dns",
                        "requete": {"size": 0, "query": {"bool": {"filter": [
                            {"term": {"dns.question.name": domaine}}]}},
                            "aggs": {"r": {"terms": {"field": "host.name", "size": 1}}}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
                {
                    "cle": "domaine", "libelle": "Domaine interrogé", "valeur": domaine,
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": "network.dns",
                        # Les domaines de l'organisation sont eux aussi en
                        # « .test » : les exclure est précisément ce que fait un
                        # analyste, qui écarte d'abord ce qui est connu interne.
                        "requete": {"size": 0, "query": {"bool": {
                            "filter": [
                                {"term": {"host.name": poste["nom"]}},
                                {"wildcard": {"dns.question.name": "*.test"}}],
                            "must_not": [
                                {"term": {"dns.question.registered_domain": "meridien.test"}}]}},
                            "aggs": {"r": {"terms": {"field": "dns.question.name", "size": 1}}}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
                {
                    "cle": "periode_minutes", "libelle": "Période, en minutes",
                    "valeur": periode, "type": "entier_tolerance", "tolerance": 1,
                    "normalisation": "entier",
                    "controle": {
                        "dataset": "network.dns",
                        "requete": {"size": 500, "sort": [{"@timestamp": "asc"}],
                                    "_source": ["@timestamp"],
                                    "query": {"bool": {"filter": [
                                        {"term": {"dns.question.name": domaine}}]}}},
                        "chemin": "hits.hits",
                        "transformation": "mediane_intervalle_minutes",
                    },
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# S4 — Exfiltration nocturne via le proxy
# ---------------------------------------------------------------------------

def s4_exfiltration(rng: random.Random, t0: datetime, jours: int, fuseau: str) -> dict:
    poste = rng.choice([p for p in ctx.POSTES if p["nom"].startswith(("pc-rh", "pc-dir"))])
    domaine = f"depot-partage-{rng.randrange(10, 99)}.example"
    destination = f"192.0.2.{rng.randrange(30, 200)}"

    depart = _nuit_du_milieu(t0, jours, fuseau, recul_jours=4, heure=1)
    nb = rng.randrange(60, 110)
    evenements = []
    total_octets = 0
    for i in range(nb):
        instant = depart + timedelta(seconds=int(i * rng.uniform(25, 60)))
        octets = rng.randrange(6_000_000, 14_000_000)
        total_octets += octets
        evenements.append(_fusion(_socle(instant, "proxy.web"), {
            "event": {"kind": "event", "category": ["network", "web"], "type": ["access"],
                      "action": "requete-web", "outcome": "success"},
            "url": {"domain": domaine, "path": "/televersement",
                    "full": f"https://{domaine}/televersement", "scheme": "https"},
            "http": {"request": {"method": "POST"}, "response": {"status_code": 200}},
            "host": {"name": poste["nom"], "ip": poste["ip"]},
            "user": {"name": rng.choice(ctx.COMPTES_UTILISATEURS)},
            # C'est « source.bytes », l'octet SORTANT, qui trahit l'exfiltration :
            # le trafic entrant, lui, reste ordinaire.
            "source": {"ip": poste["ip"], "bytes": octets},
            "destination": {"ip": destination, "port": 443, "bytes": rng.randrange(200, 2000)},
            "network": {"transport": "tcp", "direction": "outbound"},
            "user_agent": {"name": "Chrome"},
            "message": f"{domaine}/televersement -> 200",
        }))

    volume_mo = round(total_octets / (1024 * 1024))
    return {
        "ajouts": {"proxy.web": evenements},
        "retraits": [],
        "manifeste": {
            "id": "S4",
            "titre": "Exfiltration nocturne via le proxy",
            "recit": (
                "Un poste a téléversé un volume inhabituel vers un hébergeur externe, "
                "de nuit."
            ),
            "reponses": [
                {
                    "cle": "hote", "libelle": "Poste émetteur", "valeur": poste["nom"],
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": "proxy.web",
                        "requete": {"size": 0, "aggs": {"r": {
                            "terms": {"field": "host.name", "size": 1, "order": {"o": "desc"}},
                            "aggs": {"o": {"sum": {"field": "source.bytes"}}},
                        }}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
                {
                    "cle": "destination", "libelle": "Domaine de destination", "valeur": domaine,
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": "proxy.web",
                        "requete": {"size": 0, "aggs": {"r": {
                            "terms": {"field": "url.domain", "size": 1, "order": {"o": "desc"}},
                            "aggs": {"o": {"sum": {"field": "source.bytes"}}},
                        }}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
                {
                    "cle": "volume_mo", "libelle": "Volume sortant, en Mo",
                    "valeur": volume_mo, "type": "entier_tolerance", "tolerance": 5,
                    "normalisation": "entier, Mo",
                    "controle": {
                        "dataset": "proxy.web",
                        "requete": {"size": 0, "query": {"bool": {"filter": [
                            {"term": {"url.domain": domaine}},
                            {"term": {"host.name": poste["nom"]}}]}},
                            "aggs": {"r": {"sum": {"field": "source.bytes"}}}},
                        "chemin": "aggregations.r.value",
                        "transformation": "octets_vers_mo",
                    },
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# S5 — Trou de collecte de 2 h, S6 — source muette depuis 2 h
# ---------------------------------------------------------------------------

# Quelle source porte le trou, et quelle source se tait. Le choix n'est pas
# libre, et la relecture du troisième tour a montré pourquoi : avec six sources,
# trois portent déjà une réponse de repère — network.dns est la plus
# volumineuse, ids.alert la moins volumineuse, firewall.traffic celle des ports
# hauts —, et windows.security porte les événements de S1 comme de S7. Choisir
# l'une des trois premières donnait à S5 ou S6 la MÊME EMPREINTE qu'un repère :
# le stagiaire validait M4-E7 et M4-E8 avec une valeur relevée le matin, au
# module M1 ou M2. Choisir windows.security aurait fait disparaître des
# événements dont S1 a déjà figé les décomptes.
# Il reste linux.auth pour le trou et proxy.web pour le silence. S4 place son
# exfiltration quatre nuits en arrière, à une heure du matin : les deux
# dernières heures de proxy.web, que S6 retire, ne la touchent pas.
SOURCE_DU_TROU = "linux.auth"
SOURCE_MUETTE = "proxy.web"


def s5_trou(rng: random.Random, t0: datetime, jours: int, fuseau: str) -> dict:
    dataset = SOURCE_DU_TROU
    debut = t0 - timedelta(days=rng.randrange(3, 5), hours=rng.randrange(0, 6))
    fin = debut + timedelta(hours=2)
    return {
        "ajouts": {},
        "retraits": [(dataset, {"_intervalle": (debut, fin)})],
        "manifeste": {
            "id": "S5",
            "titre": "Trou de collecte de deux heures",
            "recit": "Une source n'a rien envoyé pendant deux heures, au milieu de la période.",
            "_fenetre": {"debut": T.iso(debut), "fin": T.iso(fin)},
            "reponses": [
                {
                    "cle": "source", "libelle": "Source concernée", "valeur": SOURCE_DU_TROU,
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": dataset,
                        "requete": {"size": 0, "track_total_hits": True,
                                    "query": {"range": {"@timestamp": {
                                        "gte": T.iso(debut), "lt": T.iso(fin)}}}},
                        "chemin": "hits.total.value",
                        "attendu_litteral": 0,
                    },
                },
                {
                    "cle": "duree_heures", "libelle": "Durée du trou, en heures", "valeur": 2,
                    "type": "entier", "normalisation": "entier",
                    "controle": {"dataset": dataset, "requete": {"size": 0}, "chemin": None},
                },
            ],
        },
    }


def s6_muette(rng: random.Random, t0: datetime, jours: int, fuseau: str) -> dict:
    dataset = SOURCE_MUETTE
    depuis = t0 - timedelta(hours=2)
    return {
        "ajouts": {},
        "retraits": [(dataset, {"_intervalle": (depuis, t0 + timedelta(days=1))})],
        "manifeste": {
            "id": "S6",
            "titre": "Source muette depuis deux heures",
            "recit": (
                "Une source n'envoie plus rien depuis deux heures. Elle ne produit donc aucun "
                "bucket : elle DISPARAÎT d'un décompte par source au lieu d'y apparaître à zéro."
            ),
            "reponses": [
                {
                    "cle": "source", "libelle": "Source muette", "valeur": SOURCE_MUETTE,
                    "type": "texte", "normalisation": "minuscules, espaces retirés",
                    "controle": {
                        "dataset": dataset,
                        "requete": {"size": 0, "aggs": {"r": {"max": {"field": "@timestamp"}}}},
                        "chemin": "aggregations.r.value",
                        "transformation": "minutes_avant_maintenant",
                        "attendu_environ": 120, "tolerance": 25,
                    },
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# S7 — Leurre : le scanner de vulnérabilités autorisé
# ---------------------------------------------------------------------------

# Comptes « par défaut » testés par un scanner de vulnérabilités. Aucun n'existe
# dans l'annuaire de l'organisation : le bruit de fond ne les emploie jamais, ce
# qui rend le scanner identifiable sans ambiguïté par une requête.
COMPTES_PAR_DEFAUT = ["administrateur", "admin", "root", "test", "oracle", "postgres"]


def s7_leurre(rng: random.Random, t0: datetime, jours: int, fuseau: str) -> dict:
    scanner = ctx.SCANNER_AUTORISE
    depart = _nuit_du_milieu(t0, jours, fuseau, recul_jours=5, heure=1)
    # Volontairement bien plus massif que S1 : c'est ce qui rend le leurre
    # tentant. L'analyste pressé conclut à l'attaque la plus bruyante.
    nb = rng.randrange(1500, 2100)

    evenements_win, evenements_ssh = [], []
    # Équipements réseau exclus : on ne force pas de session SSH sur un pare-feu.
    cibles_win = [h for h in ctx.TOUS_LES_HOTES
                  if h["os"] == "windows" and not h.get("equipement")]
    cibles_lin = [h for h in ctx.TOUS_LES_HOTES
                  if h["os"] == "linux" and not h.get("equipement")]
    for i in range(nb):
        instant = depart + timedelta(seconds=int(i * rng.uniform(4, 11)))
        compte = rng.choice(COMPTES_PAR_DEFAUT)
        if rng.random() < 0.5:
            cible = rng.choice(cibles_win)
            evenements_win.append(_fusion(_socle(instant, "windows.security"), {
                "event": {"kind": "event", "category": ["authentication"], "type": ["start"],
                          "action": "ouverture-de-session", "code": "4625", "outcome": "failure"},
                "user": {"name": compte, "domain": ctx.DOMAINE_AD},
                "host": {"name": cible["nom"], "ip": cible["ip"], "os": {"type": "windows"}},
                "source": {"ip": scanner["ip"]},
                "winlog": {"channel": "Security", "logon": {"type": "3"}},
                "message": f"Echec d'ouverture de session pour {compte} depuis {scanner['ip']}",
            }))
        else:
            cible = rng.choice(cibles_lin)
            evenements_ssh.append(_fusion(_socle(instant, "linux.auth"), {
                "event": {"kind": "event", "category": ["authentication"], "type": ["start"],
                          "action": "connexion-ssh", "outcome": "failure"},
                "user": {"name": compte},
                "host": {"name": cible["nom"], "ip": cible["ip"], "os": {"type": "linux"}},
                "source": {"ip": scanner["ip"], "port": rng.randrange(32768, 60999)},
                "process": {"name": "sshd", "pid": rng.randrange(400, 32000)},
                "message": f"Failed password for {compte} from {scanner['ip']} port 22 ssh2",
            }))

    return {
        "ajouts": {"windows.security": evenements_win, "linux.auth": evenements_ssh},
        "retraits": [],
        "manifeste": {
            "id": "S7",
            "titre": "Leurre : échecs massifs d'authentification",
            "recit": (
                "Une adresse interne a produit des centaines d'échecs d'authentification en une "
                "nuit, sur de nombreux hôtes. Le volume dépasse de loin celui de la vraie attaque."
            ),
            "reponses": [
                {
                    "cle": "verdict", "libelle": "Verdict", "valeur": "faux positif",
                    "type": "choix",
                    "choix": ["incident avéré", "faux positif", "information insuffisante"],
                    "normalisation": "minuscules, accents retirés, espaces retirés",
                    "controle": {
                        "dataset": "windows.security", "requete": {"size": 0}, "chemin": None,
                    },
                },
                {
                    "cle": "preuve_ip", "libelle": "Adresse à l'origine des échecs",
                    "valeur": scanner["ip"], "type": "ip", "normalisation": "espaces retirés",
                    "controle": {
                        "dataset": "windows.security",
                        "requete": {"size": 0, "query": {"bool": {"filter": [
                            {"term": {"event.code": "4625"}},
                            {"terms": {"user.name": COMPTES_PAR_DEFAUT}}]}},
                            "aggs": {"r": {"terms": {"field": "source.ip", "size": 1}}}},
                        "chemin": "aggregations.r.buckets.0.key",
                    },
                },
            ],
            "element_de_contexte": (
                "La fiche de contexte désigne cette adresse comme celle du scanner de "
                "vulnérabilités autorisé, dont le balayage hebdomadaire est planifié la nuit."
            ),
        },
    }


# L'ORDRE COMPTE. Les retraits sont appliqués au fur et à mesure : un scénario
# qui creuse un trou doit donc passer APRÈS ceux qui déposent des événements
# dans la même source, sans quoi le trou se rebouche derrière lui. S7 dépose son
# leurre sur linux.auth, où S5 creuse : il passe avant.
TOUS = [s1_force_brute, s2_balayage, s3_balise, s4_exfiltration, s7_leurre, s5_trou, s6_muette]
