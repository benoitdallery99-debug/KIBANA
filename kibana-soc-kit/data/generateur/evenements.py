"""Fabrication des événements ECS : bruit de fond des six sources, puis
injection des sept scénarios cachés — SPEC §5.2 et §5.3.

Deux règles gouvernent ce module :
- Les réponses attendues ne sont jamais écrites à la main : elles sont
  RELEVÉES sur les données effectivement produites, et vérifiées ensuite par
  une requête DSL sur le lab (CLAUDE.md, « définition de fini »).
- Le mapping est « dynamic: strict » : tout champ émis ici doit exister dans
  data/generateur/gabarits.py, sinon l'indexation est refusée.
"""

from __future__ import annotations

import random
from datetime import datetime

import contexte as ctx
import temps as T
from gabarits import ECS_VERSION

# --- Briques communes -------------------------------------------------------

def _socle(instant: datetime, dataset: str) -> dict:
    return {
        "@timestamp": T.iso(instant),
        "ecs": {"version": ECS_VERSION},
        "event": {"dataset": dataset, "module": dataset.split(".")[0]},
        "organization": {"name": ctx.ORGANISATION},
    }


def _fusion(socle: dict, ajouts: dict) -> dict:
    """Fusion récursive peu profonde, pour enrichir « event », « host »…"""
    for cle, valeur in ajouts.items():
        if isinstance(valeur, dict) and isinstance(socle.get(cle), dict):
            socle[cle] = {**socle[cle], **valeur}
        else:
            socle[cle] = valeur
    return socle


def _postes(rng: random.Random) -> dict:
    return rng.choice(ctx.POSTES)


def _hotes_windows() -> list[dict]:
    return [h for h in ctx.TOUS_LES_HOTES if h["os"] == "windows"]


def _hotes_linux() -> list[dict]:
    return [h for h in ctx.TOUS_LES_HOTES if h["os"] == "linux"]


# --- Bruit de fond : authentification Windows -------------------------------

def windows_security(rng: random.Random, instants: list[datetime]) -> list[dict]:
    """Ouvertures de session réussies, et erreurs de mot de passe bénignes.

    Le bruit bénin (mots de passe ratés) est indispensable : sans lui, la force
    brute du scénario S1 sauterait aux yeux sans qu'aucune recherche soit
    nécessaire, et l'exercice n'apprendrait rien.
    """
    hotes = _hotes_windows()
    evenements = []
    for instant in instants:
        hote = rng.choice(hotes)
        compte = rng.choice(ctx.COMPTES_UTILISATEURS + ctx.COMPTES_ADMIN)
        poste = _postes(rng)
        rate = rng.random() < 0.06  # ~6 % d'erreurs de saisie : ordinaire
        code = "4625" if rate else "4624"
        evenements.append(_fusion(_socle(instant, "windows.security"), {
            "event": {
                "kind": "event",
                "category": ["authentication"],
                "type": ["start"],
                "action": "ouverture-de-session",
                "code": code,
                "outcome": "failure" if rate else "success",
            },
            "user": {"name": compte, "domain": ctx.DOMAINE_AD},
            "host": {"name": hote["nom"], "ip": hote["ip"], "os": {"type": "windows"}},
            "source": {"ip": poste["ip"]},
            "winlog": {"channel": "Security", "logon": {"type": "3"}},
            "message": (
                f"Echec d'ouverture de session pour {compte} depuis {poste['ip']}"
                if rate else
                f"Ouverture de session reussie pour {compte} depuis {poste['ip']}"
            ),
        }))
    return evenements


# --- Bruit de fond : authentification SSH -----------------------------------

def linux_auth(rng: random.Random, instants: list[datetime]) -> list[dict]:
    hotes = _hotes_linux()
    comptes = ctx.COMPTES_ADMIN + [c["nom"] for c in ctx.COMPTES_DE_SERVICE]
    evenements = []
    for instant in instants:
        hote = rng.choice(hotes)
        compte = rng.choice(comptes)
        source = rng.choice(ctx.POSTES)["ip"] if rng.random() < 0.7 else "172.16.5.30"
        rate = rng.random() < 0.05
        evenements.append(_fusion(_socle(instant, "linux.auth"), {
            "event": {
                "kind": "event",
                "category": ["authentication"],
                "type": ["start"],
                "action": "connexion-ssh",
                "outcome": "failure" if rate else "success",
            },
            "user": {"name": compte},
            "host": {"name": hote["nom"], "ip": hote["ip"], "os": {"type": "linux"}},
            "source": {"ip": source, "port": rng.randrange(32768, 60999)},
            "process": {"name": "sshd", "pid": rng.randrange(400, 32000)},
            "message": (
                f"Failed password for {compte} from {source} port 22 ssh2"
                if rate else
                f"Accepted password for {compte} from {source} port 22 ssh2"
            ),
        }))
    return evenements


# --- Bruit de fond : alertes IDS --------------------------------------------

SIGNATURES = [
    ("ET SCAN Balayage TCP detecte", "2001219", 2, "Discovery"),
    ("ET POLICY Telechargement executable non signe", "2018959", 2, "Command and Control"),
    ("ET INFO Requete DNS vers domaine recemment enregistre", "2027865", 1, "Command and Control"),
    ("ET WEB Tentative d'injection SQL", "2006446", 3, "Initial Access"),
    ("ET MALWARE Balise periodique suspecte", "2404300", 3, "Command and Control"),
    ("ET POLICY Protocole non autorise sur port standard", "2010937", 1, "Defense Evasion"),
    ("ET EXPLOIT Tentative d'exploitation SMB", "2025649", 4, "Lateral Movement"),
    ("ET INFO Authentification en clair", "2012887", 1, "Credential Access"),
]


def ids_alert(rng: random.Random, instants: list[datetime]) -> list[dict]:
    evenements = []
    for instant in instants:
        nom, identifiant, gravite, tactique = rng.choice(SIGNATURES)
        interne = rng.random() < 0.55
        src = rng.choice(ctx.POSTES)["ip"] if interne else f"192.0.2.{rng.randrange(1, 254)}"
        dst = rng.choice(ctx.HOTES)["ip"]
        evenements.append(_fusion(_socle(instant, "ids.alert"), {
            "event": {
                "kind": "alert",
                "category": ["network", "intrusion_detection"],
                "type": ["info"],
                "outcome": "unknown",
                "severity": gravite,
            },
            "rule": {"id": identifiant, "name": nom, "category": tactique},
            "threat": {"tactic": {"name": tactique}},
            "observer": {"type": "ids", "name": "ids-perimetre-01", "vendor": "Suricata"},
            "source": {"ip": src, "port": rng.randrange(1024, 65535)},
            "destination": {"ip": dst, "port": rng.choice([80, 443, 445, 3389, 22, 1433])},
            "network": {"transport": "tcp", "direction": "internal" if interne else "inbound"},
            "message": f"{nom} ({src} -> {dst})",
        }))
    return evenements


# --- Bruit de fond : DNS ----------------------------------------------------

def network_dns(rng: random.Random, instants: list[datetime]) -> list[dict]:
    resolveur = "10.20.1.10"
    evenements = []
    for instant in instants:
        poste = _postes(rng)
        domaine = rng.choice(ctx.DOMAINES_LEGITIMES)
        # NXDOMAIN bénins : fautes de frappe, suffixes de recherche.
        nxdomain = rng.random() < 0.07
        nom = f"typo-{rng.randrange(1000, 9999)}.example" if nxdomain else domaine
        evenements.append(_fusion(_socle(instant, "network.dns"), {
            "event": {
                "kind": "event",
                "category": ["network"],
                "type": ["protocol"],
                "action": "requete-dns",
                "outcome": "failure" if nxdomain else "success",
            },
            "dns": {
                "question": {
                    "name": nom,
                    "type": "A",
                    "registered_domain": ".".join(nom.split(".")[-2:]),
                },
                "response_code": "NXDOMAIN" if nxdomain else "NOERROR",
            },
            "host": {"name": poste["nom"], "ip": poste["ip"]},
            "source": {"ip": poste["ip"]},
            "destination": {"ip": resolveur, "port": 53},
            "network": {"transport": "udp", "protocol": "dns"},
            "message": f"Requete DNS {nom} depuis {poste['ip']}",
        }))
    return evenements


# --- Bruit de fond : proxy web ----------------------------------------------

CHEMINS = ["/", "/accueil", "/api/v1/etat", "/documents", "/recherche", "/static/app.js"]


def proxy_web(rng: random.Random, instants: list[datetime]) -> list[dict]:
    evenements = []
    for instant in instants:
        poste = _postes(rng)
        domaine = rng.choice(ctx.DOMAINES_LEGITIMES)
        chemin = rng.choice(CHEMINS)
        introuvable = rng.random() < 0.05  # 404 bénins
        code = 404 if introuvable else rng.choice([200, 200, 200, 204, 301, 302])
        evenements.append(_fusion(_socle(instant, "proxy.web"), {
            "event": {
                "kind": "event",
                "category": ["network", "web"],
                "type": ["access"],
                "action": "requete-web",
                "outcome": "failure" if introuvable else "success",
            },
            "url": {
                "domain": domaine,
                "path": chemin,
                "full": f"https://{domaine}{chemin}",
                "scheme": "https",
            },
            "http": {
                "request": {"method": rng.choice(["GET", "GET", "GET", "POST"])},
                "response": {"status_code": code},
            },
            "host": {"name": poste["nom"], "ip": poste["ip"]},
            "user": {"name": rng.choice(ctx.COMPTES_UTILISATEURS)},
            "source": {"ip": poste["ip"], "bytes": rng.randrange(200, 9000)},
            "destination": {
                "ip": rng.choice(ctx.EXTERNES_LEGITIMES),
                "port": 443,
                "bytes": rng.randrange(500, 180000),
            },
            "network": {"transport": "tcp", "direction": "outbound"},
            "user_agent": {"name": rng.choice(["Firefox", "Chrome", "Edge"])},
            "message": f"{domaine}{chemin} -> {code}",
        }))
    return evenements


# --- Bruit de fond : pare-feu -----------------------------------------------

def firewall_traffic(rng: random.Random, instants: list[datetime]) -> list[dict]:
    evenements = []
    for instant in instants:
        poste = _postes(rng)
        refuse = rng.random() < 0.18
        serveur = rng.choice(ctx.HOTES)
        evenements.append(_fusion(_socle(instant, "firewall.traffic"), {
            "event": {
                "kind": "event",
                "category": ["network"],
                "type": ["connection"],
                "action": "deny" if refuse else "allow",
                "outcome": "failure" if refuse else "success",
            },
            "rule": {
                "id": "FW-020" if refuse else "FW-001",
                "name": "Blocage par defaut" if refuse else "Sortie autorisee",
            },
            "source": {"ip": poste["ip"], "port": rng.randrange(32768, 60999)},
            "destination": {
                "ip": serveur["ip"],
                "port": rng.choice([80, 443, 445, 3389, 22, 1433, 8080]),
            },
            "network": {
                "transport": rng.choice(["tcp", "tcp", "tcp", "udp"]),
                "direction": "internal",
            },
            "host": {"name": "fw-perimetre-01", "ip": "10.30.0.1"},
            "message": f"{'DENY' if refuse else 'ALLOW'} {poste['ip']} -> {serveur['ip']}",
        }))
    return evenements


GENERATEURS = {
    "windows.security": windows_security,
    "linux.auth": linux_auth,
    "ids.alert": ids_alert,
    "network.dns": network_dns,
    "proxy.web": proxy_web,
    "firewall.traffic": firewall_traffic,
}
