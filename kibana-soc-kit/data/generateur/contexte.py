"""Contexte fictif de l'organisation — SPEC §5.4.

Aucune ressemblance avec une organisation existante. Toutes les adresses sont
réservées à la documentation : RFC 5737 pour l'externe (192.0.2.0/24,
198.51.100.0/24, 203.0.113.0/24), RFC 1918 pour l'interne, RFC 2606 pour les
domaines (.test, .example). Les personnes sont inventées.

Cette fiche est reprise telle quelle dans le guide : le stagiaire enquête comme
en SOC réel, avec un plan d'adressage et des comptes de service sous les yeux.
La clé du scénario S7 (le leurre) s'y trouve : l'adresse du scanner de
vulnérabilités autorisé.
"""

from __future__ import annotations

ORGANISATION = "Groupe Méridien"
DOMAINE_AD = "MERIDIEN"

# --- Plan d'adressage -------------------------------------------------------
SOUS_RESEAUX = {
    "postes": {
        "cidr": "10.10.0.0/16",
        "role": "Postes de travail des collaborateurs",
    },
    "serveurs": {
        "cidr": "10.20.0.0/16",
        "role": "Serveurs internes : annuaire, fichiers, applications métier",
    },
    "dmz": {
        "cidr": "10.30.0.0/24",
        "role": "DMZ : portail web et relais de messagerie, exposés depuis Internet",
    },
    "administration": {
        "cidr": "172.16.5.0/24",
        "role": "Réseau d'administration : supervision, sauvegarde, scanner de vulnérabilités",
    },
}

# --- Hôtes (environ 20, SPEC §5.1) ------------------------------------------
# Chaque hôte : nom, adresse, zone, criticité. Les serveurs critiques sont ceux
# dont la compromission ferait l'objet d'une escalade immédiate.
HOTES: list[dict] = [
    {"nom": "srv-ad-01", "ip": "10.20.1.10", "zone": "serveurs", "os": "windows", "critique": True,
     "role": "Contrôleur de domaine Active Directory"},
    {"nom": "srv-ad-02", "ip": "10.20.1.11", "zone": "serveurs", "os": "windows", "critique": True,
     "role": "Contrôleur de domaine secondaire"},
    {"nom": "srv-fic-01", "ip": "10.20.2.20", "zone": "serveurs", "os": "windows", "critique": True,
     "role": "Serveur de fichiers"},
    {"nom": "srv-app-01", "ip": "10.20.3.30", "zone": "serveurs", "os": "linux", "critique": True,
     "role": "Application métier (facturation)"},
    {"nom": "srv-app-02", "ip": "10.20.3.31", "zone": "serveurs", "os": "linux", "critique": False,
     "role": "Application métier (recette)"},
    {"nom": "srv-bdd-01", "ip": "10.20.4.40", "zone": "serveurs", "os": "linux", "critique": True,
     "role": "Base de données de production"},
    {"nom": "srv-sauv-01", "ip": "172.16.5.20", "zone": "administration", "os": "linux",
     "critique": True, "role": "Serveur de sauvegarde"},
    {"nom": "srv-sup-01", "ip": "172.16.5.30", "zone": "administration", "os": "linux",
     "critique": False, "role": "Supervision"},
    {"nom": "srv-scan-01", "ip": "172.16.5.99", "zone": "administration", "os": "linux",
     "critique": False, "role": "Scanner de vulnérabilités autorisé"},
    {"nom": "web-dmz-01", "ip": "10.30.0.10", "zone": "dmz", "os": "linux", "critique": True,
     "role": "Portail web public"},
    {"nom": "smtp-dmz-01", "ip": "10.30.0.20", "zone": "dmz", "os": "linux", "critique": False,
     "role": "Relais de messagerie"},
]
# Postes de travail : complétés dynamiquement pour atteindre une vingtaine d'hôtes.
POSTES = [
    {"nom": f"pc-{service}-{numero:02d}", "ip": f"10.10.{bloc}.{numero + 20}",
     "zone": "postes", "os": "windows", "critique": False,
     "role": f"Poste de travail — {libelle}"}
    for bloc, service, libelle, plage in (
        (11, "compta", "comptabilité", range(1, 4)),
        (12, "rh", "ressources humaines", range(1, 3)),
        (13, "tech", "bureau d'études", range(1, 4)),
        (14, "dir", "direction", range(1, 2)),
    )
    for numero in plage
]
TOUS_LES_HOTES = HOTES + POSTES

# --- Comptes (environ 50, SPEC §5.1) ----------------------------------------
PRENOMS = [
    "camille", "louise", "hugo", "nadia", "yanis", "sofia", "malik", "eva",
    "tom", "lina", "noah", "jade", "adam", "chloe", "elias", "manon",
    "rayan", "zoe", "ilan", "lena", "sacha", "maya", "theo", "alba",
    "nolan", "romy", "ethan", "juliette", "gabin", "anais",
]
NOMS = [
    "bertin", "delaunay", "fauvel", "gauthier", "hamon", "jourdan", "lemoine",
    "marchand", "noirot", "ollivier", "pasquier", "renaudin", "sabatier",
    "tissier", "vasseur", "weber", "aubriot", "bonnefoy", "carrere", "dufour",
    "estève", "ferrand", "guibert", "heurtin", "isnard", "joubert", "kessler",
    "lagarde", "mercier", "navarro",
]
# 43 comptes nominatifs, engendrés par un appariement déterministe des deux
# listes : avec les comptes de service et d'administration, l'organisation
# compte 50 comptes, l'ordre de grandeur demandé par SPEC §5.1.
def _comptes_nominatifs(combien: int = 43) -> list[str]:
    vus: list[str] = []
    for i in range(combien * 3):
        compte = f"{PRENOMS[i % len(PRENOMS)]}.{NOMS[(i * 7 + i // len(NOMS)) % len(NOMS)]}"
        if compte not in vus:
            vus.append(compte)
        if len(vus) == combien:
            break
    return vus


COMPTES_UTILISATEURS = _comptes_nominatifs()

# Comptes de service : cibles privilégiées d'une attaque, et point de bascule du
# scénario S1. Le compte visé est choisi par le générateur, jamais écrit ici.
COMPTES_DE_SERVICE = [
    {"nom": "svc-sauvegarde", "role": "Compte de service — sauvegardes nocturnes"},
    {"nom": "svc-supervision", "role": "Compte de service — collecte de supervision"},
    {"nom": "svc-facturation", "role": "Compte de service — application de facturation"},
    {"nom": "svc-annuaire", "role": "Compte de service — synchronisation d'annuaire"},
]
COMPTES_ADMIN = ["adm.bertin", "adm.lemoine", "adm.weber"]

TOUS_LES_COMPTES = (
    COMPTES_UTILISATEURS
    + [c["nom"] for c in COMPTES_DE_SERVICE]
    + COMPTES_ADMIN
)

# --- Éléments clés pour l'enquête -------------------------------------------
# Le scanner autorisé : c'est lui qui rend S7 « faux positif ». Son adresse est
# donnée au stagiaire dans la fiche de contexte du guide — encore faut-il qu'il
# pense à la consulter.
SCANNER_AUTORISE = {
    "nom": "srv-scan-01",
    "ip": "172.16.5.99",
    "role": "Scanner de vulnérabilités autorisé",
    "fenetre": "Balayage hebdomadaire planifié, la nuit du mardi au mercredi",
    "contact": "Équipe Sécurité Opérationnelle",
}

# Domaines légitimes fréquentés par l'organisation (bruit de fond du proxy/DNS).
DOMAINES_LEGITIMES = [
    "portail.meridien.test", "intranet.meridien.test", "messagerie.meridien.test",
    "maj.editeur-logiciel.example", "cdn.contenu-statique.example",
    "actualites.presse-pro.example", "meteo.service-public.example",
    "annuaire.partenaire-rh.example", "banque.tresorerie.example",
    "formation.organisme.example", "recherche.moteur.example",
    "cartes.navigation.example", "video.conference.example",
]

# Adresses externes légitimes (RFC 5737 — réservées à la documentation).
EXTERNES_LEGITIMES = [f"203.0.113.{n}" for n in range(10, 40)]


def fiche_contexte() -> dict:
    """Fiche reprise dans le guide (SPEC §5.4)."""
    return {
        "organisation": ORGANISATION,
        "domaine_ad": DOMAINE_AD,
        "sous_reseaux": SOUS_RESEAUX,
        "hotes": TOUS_LES_HOTES,
        "comptes_de_service": COMPTES_DE_SERVICE,
        "comptes_admin": COMPTES_ADMIN,
        "nombre_de_comptes": len(TOUS_LES_COMPTES),
        "scanner_autorise": SCANNER_AUTORISE,
        "avertissement": (
            "Données entièrement fictives. Adresses réservées à la documentation "
            "(RFC 5737, RFC 1918) et domaines réservés (RFC 2606)."
        ),
    }
