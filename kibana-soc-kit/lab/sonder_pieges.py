"""Éprouve dans le lab chaque piège que le parcours fera rencontrer — SPEC §6.3.

Un piège enseigné doit être un piège CONSTATÉ, dans cette version et dans cette
locale. Ce script tape chaque requête dans Discover comme le ferait un stagiaire
et relève ce qui se passe vraiment : nombre de résultats, message d'erreur.

Écrit docs/pieges-lab.json, qui sert ensuite de référence au parcours (P3) et à
sa vérification : le guide ne peut affirmer que ce que ce relevé montre.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
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


# Ce que chaque forme de requête suppose du TYPE du champ. Le parcours publie un
# tableau qui l'énonce (parcours/M1.md, « Chacune de ces formes suppose quelque
# chose du champ ») ; il a longtemps dit « tout sauf un champ de type ip », ce
# qui est faux : Elasticsearch refuse le joker de début sur tout ce qui n'est ni
# keyword, ni text, ni wildcard — donc aussi sur un nombre et sur une date. Ces
# sondes-là ne sont pas des pièges du parcours : aucun exercice ne les provoque.
# Elles sont la source du tableau, relevée plutôt que rédigée de mémoire.
SONDES_DE_TYPE = [
    {"id": "joker-sur-keyword", "forme": "joker", "type_de_champ": "keyword",
     "requete": "event.dataset : network*"},
    {"id": "joker-sur-long", "forme": "joker", "type_de_champ": "long",
     "requete": "destination.port : 44*"},
    {"id": "joker-sur-date", "forme": "joker", "type_de_champ": "date",
     "requete": "@timestamp : 2026*"},
    {"id": "joker-sur-ip", "forme": "joker", "type_de_champ": "ip",
     "requete": 'destination.ip : 198.51*'},
    {"id": "comparaison-sur-long", "forme": "comparaison", "type_de_champ": "long",
     "requete": "destination.port >= 1025"},
    {"id": "comparaison-sur-date", "forme": "comparaison", "type_de_champ": "date",
     "requete": '@timestamp >= "2026-09-20"'},
    {"id": "comparaison-sur-keyword", "forme": "comparaison", "type_de_champ": "keyword",
     "requete": 'event.dataset >= "n"'},
    {"id": "comparaison-sur-ip", "forme": "comparaison", "type_de_champ": "ip",
     "requete": 'source.ip >= "10.0.0.0"'},
]


def relever_filtre_de_type(page) -> dict:
    """Piège SPEC §6.3 : « 0 champ disponible » quand un filtre de type est actif.

    Le stagiaire ouvre le filtre de type de la barre latérale pour « voir les
    champs », coche un type que rien ne porte, et se retrouve devant une liste
    vide — alors que les documents, eux, sont toujours là. Il en conclut que la
    data view est vide.

    On relève les deux états plutôt que de les affirmer.
    """
    K.ouvrir_discover(page, plage_debut="now-7d", plage_fin="now")
    page.wait_for_timeout(2_500)

    def nb_champs() -> int | None:
        el = page.query_selector(
            '[data-test-subj="fieldListGroupedAvailableFields-count"]'
        )
        if el is None:
            return None
        texte = (el.inner_text() or "").strip()
        return int(texte) if texte.isdigit() else None

    avant = nb_champs()

    bouton = page.query_selector(
        '[data-test-subj="fieldListFiltersFieldTypeFilterToggle"]'
    )
    if bouton is None:
        return {"releve": False, "raison": "bouton de filtre de type introuvable"}
    bouton.click()
    page.wait_for_timeout(1_500)

    options = page.query_selector_all('[data-test-subj^="typeFilter-"]')
    if not options:
        return {"releve": False, "raison": "aucune option de type dans le panneau"}

    # On essaie chaque type et on garde celui qui réduit le plus la liste : le
    # piège frappe d'autant plus fort que l'écart est grand, et on préfère
    # mesurer lequel c'est plutôt que de le supposer.
    meilleur = None
    for option in options:
        nom = (option.get_attribute("data-test-subj") or "").removeprefix("typeFilter-")
        option.click()
        page.wait_for_timeout(1_200)
        restant = nb_champs()
        option.click()  # on décoche avant d'essayer le suivant
        page.wait_for_timeout(600)
        if restant is not None and (meilleur is None or restant < meilleur[1]):
            meilleur = (nom, restant)
    if meilleur is None:
        return {"releve": False, "raison": "décompte des champs illisible"}

    type_choisi, _ = meilleur
    cible = page.query_selector(f'[data-test-subj="typeFilter-{type_choisi}"]')
    cible.click()
    page.wait_for_timeout(2_000)

    apres = nb_champs()
    documents = K.nombre_de_resultats(page)
    page.keyboard.press("Escape")
    if avant is None or apres is None:
        # Sans les deux décomptes, on n'a RIEN mesuré : le dire, plutôt que
        # d'écrire un piège au conditionnel dans un fichier qui sert de preuve.
        return {
            "releve": False,
            "raison": (
                "décompte des champs illisible "
                f"(avant={avant}, après={apres}) — sélecteur à reprendre"
            ),
        }
    return {
        "releve": True,
        "type_coche": type_choisi,
        "champs_avant_filtre": avant,
        "champs_apres_filtre": apres,
        "documents_toujours_affiches": documents,
    }


def relever_recherche_globale(page, terme: str) -> dict:
    """Piège SPEC §6.3 : la recherche globale n'est pas la barre de requête.

    Elle cherche des applications et des objets enregistrés, jamais le contenu
    des documents. Un stagiaire qui y tape un nom de machine n'obtient rien et
    en conclut que la machine n'existe pas.
    """
    K.ouvrir_discover(page, plage_debut="now-7d", plage_fin="now")
    page.wait_for_timeout(2_000)
    bouton = page.query_selector('[data-test-subj="nav-search-button"]')
    if bouton:
        bouton.click()
        page.wait_for_timeout(1_000)
    champ = page.query_selector('[data-test-subj="nav-search-input"]')
    if champ is None:
        return {"releve": False, "raison": "champ de recherche globale introuvable"}
    champ.fill(terme)
    page.wait_for_timeout(2_500)
    resultats = [
        (el.inner_text() or "").strip().split("\n")[0]
        for el in page.query_selector_all('[data-test-subj^="nav-search-option"]')
    ]
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    return {
        "releve": True,
        "terme": terme,
        "resultats_de_la_recherche_globale": resultats[:8],
        "documents_trouves_par_la_barre_de_requete": K.compter_avec_kql(
            page, f'host.name : "{terme}"'
        ),
    }


def relever_plage(page, debut: str, fin: str = "now") -> dict:
    """Ouvre Discover sur une plage donnée, sans requête, et compte."""
    K.ouvrir_discover(page, plage_debut=debut, plage_fin=fin)
    page.wait_for_timeout(1500)
    return {
        "plage": f"{debut} → {fin}",
        "nombre_de_resultats": K.nombre_de_resultats(page),
    }


def relever(page, requete: str) -> dict:
    nombre = K.compter_avec_kql(page, requete)
    page.wait_for_timeout(800)
    corps = page.inner_text("body")
    erreur = None
    for ligne in corps.split("\n"):
        ligne = ligne.strip()
        # Un bandeau d'erreur de Kibana est COURT. Une ligne de plusieurs
        # centaines de caractères est un document déplié, pas un message :
        # c'est ainsi qu'un vidage entier de document s'est retrouvé dans
        # docs/pieges-lab.json, pris pour un message d'erreur.
        if not ligne or len(ligne) > 200:
            continue
        # Et le mot doit être un MOT. « NOERROR », qui est un code de réponse
        # DNS parfaitement normal, contient « error » : c'était lui, le
        # coupable.
        if re.search(r"\b(impossible d|erreurs?|errors?|invalide)\b", ligne, re.I):
            erreur = ligne
            break
    return {
        "requete": requete,
        "nombre_de_resultats": nombre,
        "message_affiche": erreur,
        "aboutit": nombre is not None,
    }


AGE_MINIMAL_DONNEES_MIN = 20


def age_des_donnees_en_minutes() -> float | None:
    """Depuis combien de temps le jeu de données a-t-il été chargé ?

    Le générateur ancre la fin de la fenêtre sur l'instant du chargement. Juste
    après « make data », les quinze dernières minutes contiennent donc des
    documents, et le piège « la plage par défaut ne montre rien » se relèverait
    FAUX — c'est arrivé : 94 documents au lieu de zéro, dans un fichier qui sert
    de preuve au parcours. On refuse de relever plutôt que d'écrire cela.
    """
    chemin = conf.RACINE / "data" / "manifest.json"
    if not chemin.exists():
        return None
    engendre = json.loads(chemin.read_text(encoding="utf-8")).get("engendre_le")
    if not engendre:
        return None
    instant = datetime.fromisoformat(engendre)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)
    return (datetime.now(UTC) - instant).total_seconds() / 60


def main() -> int:
    age = age_des_donnees_en_minutes()
    if age is not None and age < AGE_MINIMAL_DONNEES_MIN:
        raise SystemExit(
            f"Données chargées il y a {age:.0f} min ; il en faut "
            f"{AGE_MINIMAL_DONNEES_MIN} pour relever le piège de la plage par "
            f"défaut, qui n'est vide qu'une fois ce délai passé.\n"
            f"Attendez {AGE_MINIMAL_DONNEES_MIN - age:.0f} min, puis relancez."
        )

    releve = {
        "version_stack": conf.version(),
        "locale": str(conf.valeur("kibana.locale")),
        "avertissement": (
            "Relevé dans Discover, requête tapée au clavier comme le ferait un stagiaire. "
            "Le parcours ne peut affirmer que ce que montre ce fichier."
        ),
        "pieges": [],
        "sondes_de_type": [],
    }
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        K.ouvrir_discover(page)
        for piege in PIEGES:
            entree = {k: v for k, v in piege.items() if k not in ("fautive", "juste")}
            entree["type"] = "requete"
            entree["ce_qui_echoue"] = relever(page, piege["fautive"])
            entree["ce_qui_marche"] = relever(page, piege["juste"])
            releve["pieges"].append(entree)
            print(f"  {piege['id']:26s} "
                  f"fautive={entree['ce_qui_echoue']['nombre_de_resultats']!s:>8}  "
                  f"juste={entree['ce_qui_marche']['nombre_de_resultats']!s:>8}"
                  + (f"  « {entree['ce_qui_echoue']['message_affiche'][:52]} »"
                     if entree["ce_qui_echoue"]["message_affiche"] else ""))
        for sonde in SONDES_DE_TYPE:
            releve_sonde = relever(page, sonde["requete"])
            releve["sondes_de_type"].append({**sonde, **releve_sonde})
            print(f"  {sonde['id']:26s} "
                  f"résultats={releve_sonde['nombre_de_resultats']!s:>8}"
                  + (f"  « {releve_sonde['message_affiche'][:52]} »"
                     if releve_sonde["message_affiche"] else ""))

    # Le piège d'ouverture du parcours : la plage de temps par défaut de Kibana
    # est bien trop courte pour un jeu de données de sept jours. On mesure les
    # deux, plutôt que de l'affirmer.
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        defaut = relever_plage(page, "now-15m")
        large = relever_plage(page, "now-7d")
    releve["pieges"].append({
        "id": "plage-de-temps-par-defaut",
        "type": "plage_de_temps",
        "titre": "La plage de temps par défaut est trop courte pour le jeu de données",
        "lecon": (
            "Kibana ouvre Discover sur une fenêtre très courte. Sur sept jours de données, "
            "l'écran paraît vide alors que tout est là. Avant de conclure à l'absence de "
            "données, on élargit la plage."
        ),
        "ce_qui_echoue": defaut,
        "ce_qui_marche": large,
    })
    print(f"  plage-de-temps-par-defaut  "
          f"15 min={defaut['nombre_de_resultats']}  7 j={large['nombre_de_resultats']}")

    # Les deux pièges d'INTERFACE de SPEC §6.3, que le parcours ne provoquait
    # pas encore : ils ne se relèvent pas par une requête, mais par un geste.
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        filtre = relever_filtre_de_type(page)
        globale = relever_recherche_globale(page, "fw-perimetre-01")

    releve["pieges"].append({
        "id": "filtre-de-type-de-champ",
        "type": "interface",
        "titre": "« 0 champ disponible » : un filtre de type est resté actif",
        # La leçon est ÉCRITE À PARTIR DE LA MESURE : un chiffre annoncé ici
        # doit être celui qui vient d'être relevé, pas celui qu'on espérait.
        "lecon": (
            "La barre latérale porte un filtre par type de champ. Coché, il réduit "
            "la liste des champs sans rien dire — relevé en lab : de "
            f"{filtre.get('champs_avant_filtre')} champs à "
            f"{filtre.get('champs_apres_filtre')} — alors que les documents, eux, "
            "restent affichés. Une liste de champs presque vide n'est pas une data "
            "view vide : regardez d'abord si un filtre est actif."
        ) if filtre.get("releve") else (
            "NON RELEVÉ : " + str(filtre.get("raison"))
        ),
        "ce_qui_echoue": {
            "geste": f"filtre de type « {filtre.get('type_coche')} » coché",
            "champs_affiches": filtre.get("champs_apres_filtre"),
            "documents_affiches": filtre.get("documents_toujours_affiches"),
            "aboutit": False,
        } if filtre.get("releve") else {"aboutit": False, "raison": filtre.get("raison")},
        "ce_qui_marche": {
            "geste": "aucun filtre de type",
            "champs_affiches": filtre.get("champs_avant_filtre"),
            "aboutit": True,
        } if filtre.get("releve") else {"aboutit": False, "raison": filtre.get("raison")},
    })
    print(f"  filtre-de-type-de-champ    "
          f"champs {filtre.get('champs_avant_filtre')} -> "
          f"{filtre.get('champs_apres_filtre')}, "
          f"documents {filtre.get('documents_toujours_affiches')}")

    releve["pieges"].append({
        "id": "recherche-globale-n-est-pas-la-requete",
        "type": "interface",
        "titre": "La recherche globale de Kibana ne cherche pas dans les documents",
        "lecon": (
            "La loupe du bandeau supérieur trouve des applications et des objets "
            "enregistrés. Elle ne regarde jamais le contenu des journaux. Pour "
            "chercher une valeur, c'est la barre de requête de Discover."
        ),
        "ce_qui_echoue": {
            "geste": f"« {globale.get('terme')} » tapé dans la recherche globale",
            "resultats": globale.get("resultats_de_la_recherche_globale"),
            "aboutit": False,
        } if globale.get("releve") else {"aboutit": False, "raison": globale.get("raison")},
        "ce_qui_marche": {
            "requete": f'host.name : "{globale.get("terme")}"',
            "nombre_de_resultats": globale.get(
                "documents_trouves_par_la_barre_de_requete"),
            "aboutit": True,
        } if globale.get("releve") else {"aboutit": False, "raison": globale.get("raison")},
    })
    print(f"  recherche-globale          "
          f"globale={globale.get('resultats_de_la_recherche_globale')} "
          f"requête={globale.get('documents_trouves_par_la_barre_de_requete')}")

    sortie = conf.RACINE / "docs" / "pieges-lab.json"
    sortie.write_text(json.dumps(releve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Écrit : {sortie.relative_to(conf.RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
