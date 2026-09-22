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
    # SEULS les hôtes que la fiche de contexte rend vraiment. Le gabarit du
    # guide n'affiche que « les serveurs critiques » — {% for h in
    # contexte.hotes if h.critique %} —, soit neuf machines sur vingt et une.
    # Exempter les vingt et une revenait à ne plus surveiller du tout les postes
    # de travail, et donc trois réponses de scénario sur sept : S2.source_ip,
    # S3.hote et S4.hote. Le stagiaire ne voit ces noms nulle part ; ils ne se
    # « perdent parmi leurs semblables » sur aucune page.
    for hote in contexte.get("hotes", []):
        if not hote.get("critique"):
            continue
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


# Un petit entier écrit en toutes lettres est parfaitement discriminant, là où
# le même en chiffres se rencontrerait partout. « six sources » dévoile une
# réponse ; « 6 » non. On surveille donc les deux formes, différemment.
EN_LETTRES = {
    0: "zéro", 1: "un", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq",
    6: "six", 7: "sept", 8: "huit", 9: "neuf", 10: "dix", 11: "onze",
    12: "douze", 13: "treize", 14: "quatorze", 15: "quinze", 16: "seize",
    17: "dix-sept", 18: "dix-huit", 19: "dix-neuf", 20: "vingt",
    21: "vingt et un", 30: "trente", 40: "quarante", 50: "cinquante",
}


_MOTS_VIDES = {
    "nombre", "distincts", "distinctes", "concernee", "concernée", "observes",
    "observés", "alimentent", "produit", "plus", "frequente", "fréquente",
    "durée", "duree", "dans", "pour", "avec", "cette", "celui", "视",
}


# Le libellé d'une réponse et le mot qu'emploie le guide ne sont pas toujours
# les mêmes. Le manifeste dit « hôtes », la fiche de contexte disait
# « machines » : le garde cherchait « 21 hôtes » et laissait passer
# « 21 machines ». Table courte et explicite, plutôt qu'une heuristique qui
# ferait semblant de couvrir tout le français.
_SYNONYMES = {
    "hôtes": ("machines", "postes", "équipements"),
    "hotes": ("machines", "postes"),
    "sources": ("datasets", "jeux"),
    "comptes": ("utilisateurs", "identifiants"),
    "signatures": ("règles", "alertes"),
}


def _sujets(libelle: str) -> list[str]:
    """Noms significatifs d'un libellé de réponse, pour ancrer la recherche.

    Chaque nom entraîne avec lui ses synonymes d'usage : c'est le mot du GUIDE
    qu'il faut attraper, pas celui du manifeste.
    """
    mots = re.findall(r"[A-Za-zÀ-ÿ]{5,}", libelle.lower())
    retenus = [m for m in mots if m not in _MOTS_VIDES][:3]
    sujets: list[str] = []
    for mot in retenus:
        sujets.append(mot)
        sujets.extend(_SYNONYMES.get(mot, ()))
    return sujets


def _champs(controle: Any) -> list[str]:
    """Noms de champ ECS cités par la requête de contrôle d'une réponse.

    Aucune table de synonymes ne couvrira jamais le français. Mais le nom du
    champ, lui, est un ancrage exact : une phrase qui écrit un nombre puis
    « event.dataset » à trois mots de là parle bien du décompte en question,
    quel que soit le nom commun employé entre les deux. C'est par là qu'est
    passé « vos six valeurs de event.dataset » — « valeurs » n'est le synonyme
    de rien, et ne pouvait pas l'être : il est trop courant pour être surveillé
    seul.
    """
    trouves: list[str] = []

    def descendre(noeud: Any) -> None:
        if isinstance(noeud, dict):
            for cle, valeur in noeud.items():
                if cle == "field" and isinstance(valeur, str) and "." in valeur:
                    trouves.append(valeur)
                else:
                    descendre(valeur)
        elif isinstance(noeud, list):
            for element in noeud:
                descendre(element)

    descendre(controle)
    return sorted(set(trouves))


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
            entier = reponse["type"] in ("entier", "entier_tolerance")
            if entier:
                # La forme en toutes lettres, elle, est toujours surveillée :
                # c'est ainsi qu'une réponse fuit dans une phrase.
                mot = EN_LETTRES.get(int(valeur))
                if mot:
                    # On n'attrape le mot que s'il est suivi du SUJET de la
                    # question. « six sources » dévoile la réponse ; « six
                    # modules » ou « vingt-deux heures » ne dévoilent rien.
                    # Le sujet se lit dans le libellé de la réponse.
                    for sujet in _sujets(reponse.get("libelle", "")):
                        a_surveiller.append((
                            f"{bloc['id']}.{reponse['cle']}",
                            f"{mot} {sujet}",
                            "entier_en_lettres",
                        ))
                    for champ in _champs(reponse.get("controle")):
                        a_surveiller.append((
                            f"{bloc['id']}.{reponse['cle']}",
                            f"{mot} {champ}",
                            "entier_pres_du_champ",
                        ))
                # En chiffres, un petit entier se rencontrerait partout : « 6 »
                # apparaît dans une date, une version, un identifiant. On ne le
                # cherche donc pas seul — mais on le cherche SUIVI DU SUJET de
                # la question, exactement comme la forme en toutes lettres.
                # C'est la brèche par laquelle « 21 machines » est passé dans la
                # fiche de contexte, où 21 est la réponse attendue de trois
                # exercices.
                if len(valeur) < 3:
                    for sujet in _sujets(reponse.get("libelle", "")):
                        a_surveiller.append((
                            f"{bloc['id']}.{reponse['cle']}",
                            f"{valeur} {sujet}",
                            "entier_en_lettres",
                        ))
                    for champ in _champs(reponse.get("controle")):
                        a_surveiller.append((
                            f"{bloc['id']}.{reponse['cle']}",
                            f"{valeur} {champ}",
                            "entier_pres_du_champ",
                        ))
                    continue
            a_surveiller.append((f"{bloc['id']}.{reponse['cle']}", valeur, reponse["type"]))
    return a_surveiller


# Les données encodées en base64 — polices, captures inlinées — ne sont pas du
# texte : personne n'y lira jamais une réponse. Mais leur alphabet contient
# « + » et « / », qui ne sont pas alphanumériques : une suite « +889/ » au
# milieu d'une image satisfait donc les délimiteurs d'un nombre cherché isolé.
# Constaté : une capture régénérée a fait échouer la construction sur
# S4.volume_mo, sans qu'aucune réponse n'ait fui nulle part. Un garde qui
# dépend des octets d'une image n'est pas un garde — il est un tirage au sort,
# et il peut aussi bien taire une vraie fuite dans son bruit.
_BASE64 = re.compile(r'data:[^;,\s"\']*;base64,[A-Za-z0-9+/=]+')


def sans_donnees_encodees(texte: str) -> str:
    """Retire les charges utiles base64, qui ne sont pas du texte lisible."""
    return _BASE64.sub("data:…", texte)


def chercher(texte: str, manifeste: dict[str, Any]) -> list[str]:
    """Liste les réponses trouvées en clair dans « texte »."""
    texte = sans_donnees_encodees(texte)
    fuites = []
    for cle, valeur, type_ in reponses_a_surveiller(manifeste):
        if type_ == "entier_en_lettres":
            mot, sujet = valeur.split(" ", 1)
            # Le nombre doit être isolé — « vingt-deux » ne compte pas — et
            # immédiatement suivi du sujet de la question, au singulier ou au
            # pluriel.
            trouve = re.search(
                rf"(?<![\w-]){re.escape(mot)}\s+{re.escape(sujet)}s?\b", texte, re.I
            )
        elif type_ == "entier_pres_du_champ":
            # Même règle, ancrée sur le nom du champ plutôt que sur un nom
            # commun : le nombre doit être isolé, et le champ le suivre à trois
            # mots près — la place d'un « valeurs de », d'un « sources de » ou
            # d'un « lignes du champ ».
            mot, champ = valeur.split(" ", 1)
            trouve = re.search(
                rf"(?<![\w-]){re.escape(mot)}\s+(?:\S+\s+){{0,3}}{re.escape(champ)}\b",
                texte,
                re.I,
            )
        elif type_ in ("entier", "entier_tolerance"):
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
