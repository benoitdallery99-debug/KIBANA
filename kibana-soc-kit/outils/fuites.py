"""Recherche de réponses attendues publiées en clair.

Employé par le constructeur du guide et par la vérification du parcours, pour
qu'ils appliquent EXACTEMENT la même règle.

La règle n'est pas « aucune valeur du manifeste ne doit apparaître » : ce serait
faux. SPEC §5.4 impose au contraire de publier une fiche de contexte contenant
le plan d'adressage, les serveurs critiques, les comptes de service et —
explicitement — l'adresse du scanner autorisé, qui est la clé du scénario S7.
Un analyste a cette fiche sous les yeux ; c'est la situation réelle.

La règle est donc : une réponse ne doit pas être publiée AILLEURS que dans la
fiche de contexte, où elle se perd parmi ses semblables. Savoir que
l'organisation compte quatre comptes de service ne dit pas lequel a été forcé.
"""

from __future__ import annotations

import re
from typing import Any


def valeurs_publiees_par_le_contexte(contexte: dict[str, Any]) -> set[str]:
    """Tout ce que la fiche de contexte publie légitimement."""
    publiees: set[str] = set()
    for hote in contexte.get("hotes", []):
        publiees.add(str(hote.get("nom", "")))
        publiees.add(str(hote.get("ip", "")))
    for compte in contexte.get("comptes_de_service", []):
        publiees.add(str(compte.get("nom", "")))
    publiees.update(str(c) for c in contexte.get("comptes_admin", []))
    scanner = contexte.get("scanner_autorise", {})
    publiees.add(str(scanner.get("nom", "")))
    publiees.add(str(scanner.get("ip", "")))
    for reseau in (contexte.get("sous_reseaux") or {}).values():
        publiees.add(str(reseau.get("cidr", "")))
    publiees.add(str(contexte.get("organisation", "")))
    publiees.discard("")
    return publiees


def reponses_a_surveiller(manifeste: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Renvoie (clé, valeur, type) pour chaque réponse qui ne doit pas être publiée."""
    publiees = valeurs_publiees_par_le_contexte(manifeste.get("contexte", {}))
    blocs = [manifeste["reperes"], *manifeste["scenarios"]] if "reperes" in manifeste \
        else manifeste["scenarios"]

    a_surveiller = []
    for bloc in blocs:
        for reponse in bloc["reponses"]:
            valeur = str(reponse["valeur"])
            # Un verdict (« faux positif ») fait partie de l'énoncé : on demande
            # au stagiaire de trancher entre des choix qu'il faut bien nommer.
            if reponse["type"] == "choix":
                continue
            # Une valeur que la fiche de contexte publie déjà n'est pas une fuite :
            # elle figure parmi ses semblables et ne désigne rien.
            if valeur in publiees:
                continue
            # Un entier de moins de trois chiffres ne se surveille pas par
            # recherche de texte : « 2 » ou « 70 » se rencontrent partout, et la
            # durée d'un trou de collecte fait d'ailleurs partie de l'énoncé.
            # Ces réponses restent protégées par ce qui compte vraiment : elles
            # ne sont pas calculables sans faire l'exercice.
            if reponse["type"] in ("entier", "entier_tolerance") and len(valeur) < 3:
                continue
            a_surveiller.append((f"{bloc['id']}.{reponse['cle']}", valeur, reponse["type"]))
    return a_surveiller


def chercher(texte: str, manifeste: dict[str, Any]) -> list[str]:
    """Liste les réponses trouvées en clair dans « texte »."""
    fuites = []
    for cle, valeur, type_ in reponses_a_surveiller(manifeste):
        if type_ in ("entier", "entier_tolerance"):
            # Un nombre se cherche isolé de tout caractère alphanumérique :
            # borné aux seuls chiffres, « 889 » se trouverait au milieu des
            # polices encodées en base64, où il est sans rapport.
            trouve = re.search(
                rf"(?<![0-9A-Za-z]){re.escape(valeur)}(?![0-9A-Za-z])", texte
            )
        else:
            trouve = valeur in texte
        if trouve:
            fuites.append(f"{cle} = « {valeur} »")
    return fuites
