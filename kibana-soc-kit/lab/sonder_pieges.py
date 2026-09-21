"""Éprouve dans le lab chaque piège que le parcours fera rencontrer — SPEC §6.3.

Un piège enseigné doit être un piège CONSTATÉ, dans cette version et dans cette
locale. Ce script tape chaque requête dans Discover comme le ferait un stagiaire
et relève ce qui se passe vraiment : nombre de résultats, message d'erreur.

Écrit docs/pieges-lab.json, qui sert ensuite de référence au parcours (P3) et à
sa vérification : le guide ne peut affirmer que ce que ce relevé montre.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf
from verif.e2e import kibana as K

# Chaque entrée : ce qu'on veut montrer, la requête fautive, la requête juste.
PIEGES = [
    {
        "id": "plage-lucene-en-kql",
        "titre": "La syntaxe de plage de Lucene n'existe pas en KQL",
        "fautive": 'destination.port : [1025 TO *]',
        "juste": "destination.port >= 1025",
        "lecon": (
            "« [1025 TO *] » est de la syntaxe Lucene. En KQL, elle ne veut rien dire : "
            "il faut une comparaison."
        ),
    },
    {
        "id": "exists-lucene-en-kql",
        "titre": "« _exists_ » est du Lucene ; en KQL l'existence s'écrit « champ:* »",
        "fautive": "_exists_ : rule.name",
        "juste": "rule.name : *",
        "lecon": (
            "Celui-ci est le vrai piège muet : aucune erreur, aucun résultat. "
            "Zéro résultat n'est pas une réponse, c'est une question."
        ),
    },
    {
        "id": "casse-sur-keyword",
        "titre": "Un champ keyword est sensible à la casse",
        "fautive": 'user.name : "SVC-FACTURATION"',
        "juste": 'user.name : "svc-facturation"',
        "lecon": (
            "user.name est un keyword : il est comparé tel quel, sans transformation. "
            "La casse compte."
        ),
    },
    {
        "id": "casse-sur-texte-analyse",
        "titre": "Un champ text, lui, est analysé : la casse n'y compte pas",
        "fautive": 'message : "ECHEC"',
        "juste": 'message : "echec"',
        "lecon": (
            "message est un champ text : il est découpé et mis en minuscules à l'indexation. "
            "Les deux requêtes donnent le même résultat — c'est le contraste avec le keyword."
        ),
        "attendu": "meme_resultat",
    },
    {
        "id": "cidr-sur-champ-ip",
        "titre": "Un champ de type ip prend le CIDR, et refuse le joker",
        "fautive": 'destination.ip : "10.*"',
        "juste": 'destination.ip : "10.0.0.0/8"',
        "lecon": (
            "Sur un champ de type ip, le CIDR est compris nativement. Le joker, lui, n'a pas "
            "de sens sur une adresse : constaté en lab, Discover refuse la requête au lieu "
            "de renvoyer un résultat approchant."
        ),
    },
]


def relever(page, requete: str) -> dict:
    nombre = K.compter_avec_kql(page, requete)
    page.wait_for_timeout(800)
    corps = page.inner_text("body")
    erreur = None
    for ligne in corps.split("\n"):
        ligne = ligne.strip()
        if ligne and any(
            marque in ligne.lower()
            for marque in ("impossible d", "erreur", "error", "invalide")
        ):
            erreur = ligne
            break
    return {
        "requete": requete,
        "nombre_de_resultats": nombre,
        "message_affiche": erreur,
        "aboutit": nombre is not None,
    }


def main() -> int:
    releve = {
        "version_stack": conf.version(),
        "locale": str(conf.valeur("kibana.locale")),
        "avertissement": (
            "Relevé dans Discover, requête tapée au clavier comme le ferait un stagiaire. "
            "Le parcours ne peut affirmer que ce que montre ce fichier."
        ),
        "pieges": [],
    }
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        K.ouvrir_discover(page)
        for piege in PIEGES:
            entree = {k: v for k, v in piege.items() if k not in ("fautive", "juste")}
            entree["ce_qui_echoue"] = relever(page, piege["fautive"])
            entree["ce_qui_marche"] = relever(page, piege["juste"])
            releve["pieges"].append(entree)
            print(f"  {piege['id']:26s} "
                  f"fautive={entree['ce_qui_echoue']['nombre_de_resultats']!s:>8}  "
                  f"juste={entree['ce_qui_marche']['nombre_de_resultats']!s:>8}"
                  + (f"  « {entree['ce_qui_echoue']['message_affiche'][:52]} »"
                     if entree["ce_qui_echoue"]["message_affiche"] else ""))

    sortie = conf.RACINE / "docs" / "pieges-lab.json"
    sortie.write_text(json.dumps(releve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Écrit : {sortie.relative_to(conf.RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
