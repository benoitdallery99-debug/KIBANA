"""verif-parcours — ce que prouve cette suite (SPEC §10) :

chaque réponse attendue vient du manifeste et n'est jamais écrite en clair ;
chaque requête KQL du parcours, tapée dans Discover, renvoie ce qui est annoncé ;
chaque libellé d'interface cité existe dans l'interface fr-FR du lab ;
chaque piège de SPEC §6.3 est provoqué par un exercice ; le guidage est dégressif.
"""

from __future__ import annotations

import collections
import json
import math
import re

import pytest
import yaml

from outils.fuites import chercher as chercher_fuites
from outils.libelles import ANGLAIS_ASSUME
from outils.libelles import normaliser as normaliser_libelle
from verif.e2e import kibana as K

pytestmark = pytest.mark.parcours

# Part maximale des questions dont la bonne réponse partage le même rang.
# Quatre propositions donnent 25 % au hasard pur ; au-delà d'un tiers, la
# position devient une stratégie plus payante que la lecture de la question.
PART_MAXIMALE_D_UN_RANG = 1 / 3

GUIDAGES = ("demonstration", "guide", "semi-guide", "autonome")
RANG = {g: i for i, g in enumerate(GUIDAGES)}


# --------------------------------------------------------------------------
# Chargement
# --------------------------------------------------------------------------

def _frontmatter(texte: str) -> tuple[dict, str]:
    if not texte.startswith("---"):
        raise AssertionError("frontmatter YAML absent")
    _, brut, corps = texte.split("---", 2)
    return yaml.safe_load(brut), corps


@pytest.fixture(scope="module")
def modules(config):
    fichiers = sorted((config.RACINE / "parcours").glob("M*.md"))
    if not fichiers:
        pytest.skip("NON EXÉCUTÉ : aucun module dans parcours/. Phase P3 non commencée.")
    charges = []
    for chemin in fichiers:
        entete, corps = _frontmatter(chemin.read_text(encoding="utf-8"))
        charges.append({"chemin": chemin, "entete": entete, "corps": corps})
    return charges


@pytest.fixture(scope="module")
def reponses(manifeste):
    """Index « S1.source_ip » → réponse du manifeste."""
    blocs = [manifeste["reperes"], *manifeste["scenarios"]]
    return {f"{b['id']}.{r['cle']}": r for b in blocs for r in b["reponses"]}


@pytest.fixture(scope="module")
def pieges_lab(config):
    chemin = config.RACINE / "docs" / "pieges-lab.json"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : docs/pieges-lab.json absent. Lancez lab/sonder_pieges.py.")
    return json.loads(chemin.read_text(encoding="utf-8"))


def _exercices(modules) -> list[tuple[dict, dict]]:
    return [(m, e) for m in modules for e in (m["entete"].get("exercices") or [])]


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------

def test_les_six_modules_existent(modules):
    identifiants = [m["entete"]["id"] for m in modules]
    assert identifiants == ["M0", "M1", "M2", "M3", "M4", "M5"], identifiants


def test_frontmatter_complet(modules):
    manques = []
    for m in modules:
        e = m["entete"]
        for cle in ("id", "titre", "duree_minutes", "resume", "objectifs", "exercices"):
            if not e.get(cle):
                manques.append(f"{m['chemin'].name} : « {cle} » absent ou vide")
        for objectif in e.get("objectifs") or []:
            if not objectif.get("enonce", "").startswith("À l'issue du module"):
                manques.append(
                    f"{objectif.get('id')} : l'énoncé doit commencer par « À l'issue du module »"
                )
    assert not manques, "frontmatter incomplet :\n  " + "\n  ".join(manques)


def test_les_libelles_sont_bien_des_chaines(modules):
    """Un libellé qui contient un deux-points doit être entre guillemets.

    Sans eux, YAML lit « - Language: KQL » comme une association et non comme
    une chaîne : le libellé disparaît alors des contrôles, sans erreur — une
    autre façon de rendre un contrôle décoratif.
    """
    defauts = [
        f"{e['id']} : {libelle!r}"
        for _module, e in _exercices(modules)
        for libelle in e.get("libelles_ui") or []
        if not isinstance(libelle, str)
    ]
    assert not defauts, (
        "libellés qui ne sont pas des chaînes (guillemets manquants ?) :\n  "
        + "\n  ".join(defauts)
    )


def test_identifiants_uniques(modules):
    vus: dict[str, str] = {}
    doublons = []
    for m in modules:
        for liste in ("objectifs", "exercices"):
            for element in m["entete"].get(liste) or []:
                identifiant = element["id"]
                if identifiant in vus:
                    doublons.append(f"{identifiant} ({vus[identifiant]} et {m['chemin'].name})")
                vus[identifiant] = m["chemin"].name
    assert not doublons, f"identifiants en double : {doublons}"


def test_rappel_actif_sauf_en_m0(modules):
    """SPEC §6.1 : chaque module s'ouvre sur 2 à 3 questions de rappel."""
    defauts = []
    for m in modules:
        rappel = m["entete"].get("rappel_actif") or []
        if m["entete"]["id"] == "M0":
            if rappel:
                defauts.append("M0 ne devrait pas avoir de rappel : il n'y a rien avant")
        elif not 2 <= len(rappel) <= 3:
            defauts.append(
                f"{m['entete']['id']} : {len(rappel)} question(s) de rappel, 2 à 3 attendues"
            )
    assert not defauts, "rappel actif :\n  " + "\n  ".join(defauts)


def test_guidage_degressif(modules):
    """Le guidage ne remonte jamais à l'intérieur d'un module (SPEC §6.1)."""
    defauts = []
    for m in modules:
        niveaux = [e["guidage"] for e in m["entete"]["exercices"]]
        for niveau in niveaux:
            if niveau not in GUIDAGES:
                defauts.append(f"{m['entete']['id']} : guidage « {niveau} » inconnu")
        rangs = [RANG[n] for n in niveaux if n in RANG]
        if rangs != sorted(rangs):
            defauts.append(f"{m['entete']['id']} : guidage non dégressif — {niveaux}")
    assert not defauts, "guidage :\n  " + "\n  ".join(defauts)


def test_capstone_m4_entierement_autonome(modules):
    m4 = next(m for m in modules if m["entete"]["id"] == "M4")
    niveaux = {e["guidage"] for e in m4["entete"]["exercices"]}
    assert niveaux == {"autonome"}, f"M4 doit être entièrement autonome, trouvé : {niveaux}"


def test_chaque_objectif_est_evalue_par_un_exercice(modules):
    """SPEC §2 : chaque objectif est évalué par au moins un exercice."""
    couverts = {o for _, e in _exercices(modules) for o in (e.get("objectifs") or [])}
    orphelins = [
        o["id"] for m in modules for o in m["entete"]["objectifs"] if o["id"] not in couverts
    ]
    assert not orphelins, f"objectifs sans exercice : {orphelins}"


# Vitesse de lecture retenue pour une prose technique en français, tableaux et
# blocs de code compris. Elle est GÉNÉREUSE : un modèle plus fin — prose à 180,
# quinze secondes par ligne de tableau, dix par ligne de code — donne 67 min de
# lecture sur le parcours là où celui-ci en donne 46. La durée d'un module est
# donc un plancher, jamais une promesse optimiste.
MOTS_PAR_MINUTE = 180

# Une question de rappel actif, posée et répondue à l'oral, prend une minute.
MINUTES_PAR_RAPPEL = 1

# SPEC §1 annonce « 6 h de parcours ». La borne haute la dépasse volontairement,
# et l'écart est consigné (docs/JOURNAL.md, E10) : SPEC §1 ne budgète ni la
# lecture des corps de module ni le rappel actif, que docs/CHARTE_REDACTION.md
# rend pourtant obligatoires. Mesuré, le parcours vaut 6 h 43. Le kit garde son
# contenu et dit la vraie durée plutôt que de la rogner pour rentrer dans une
# prémisse ; le déroulé minuté de formateur/guide-formateur.md donne la journée
# réelle. Ce commentaire est là pour qu'un relecteur voie la borne ET sa raison.
BORNES_DU_PARCOURS = (300, 420)


def _minutes_de_lecture(corps: str) -> int:
    """Temps de lecture du corps d'un module, arrondi à la minute supérieure."""
    return math.ceil(len(corps.split()) / MOTS_PAR_MINUTE)


def test_durees_coherentes(modules):
    """La durée d'un module doit couvrir TOUT ce qu'il demande, pas ses seuls exercices.

    Le contrôle ne regardait que la somme des exercices, et la durée annoncée
    lui était exactement égale dans quatre modules sur six : ni la lecture du
    corps ni le rappel actif n'avaient une minute, alors que la charte impose
    l'un et l'autre. Un formateur qui planifiait la journée sur ces chiffres
    dépassait de trois quarts d'heure sans savoir pourquoi.
    """
    defauts = []
    total = 0
    detail = []
    for m in modules:
        entete = m["entete"]
        annonce = entete["duree_minutes"]
        total += annonce
        exercices = sum(e.get("duree_minutes", 0) for e in entete["exercices"])
        lecture = _minutes_de_lecture(m["corps"])
        rappel = len(entete.get("rappel_actif") or []) * MINUTES_PAR_RAPPEL
        besoin = exercices + lecture + rappel
        detail.append(
            f"{entete['id']} : {exercices} ex + {lecture} lecture + {rappel} rappel "
            f"= {besoin} pour {annonce} annoncées"
        )
        if besoin > annonce:
            defauts.append(detail[-1])
    assert not defauts, (
        "durées annoncées trop courtes pour ce que le module demande :\n  "
        + "\n  ".join(defauts)
    )
    bas, haut = BORNES_DU_PARCOURS
    assert bas <= total <= haut, (
        f"parcours de {total} min, hors des bornes {bas}-{haut} (SPEC §1 et "
        f"l'écart consigné) :\n  " + "\n  ".join(detail)
    )


# --------------------------------------------------------------------------
# Les réponses viennent du manifeste, et n'apparaissent jamais en clair
# --------------------------------------------------------------------------

def test_chaque_exercice_renvoie_a_une_reponse_du_manifeste(modules, reponses):
    """Tout exercice se vérifie : par une empreinte, ou par un rendu déclaré.

    La règle d'origine — une réponse du manifeste pour tout ce qui n'est pas une
    démonstration — a servi jusqu'au capstone, où elle s'est retournée : pour
    donner une empreinte à « construisez ce tableau de bord » et à « rédigez
    cinq lignes », on avait fait valider à ces exercices une valeur relevée le
    matin. L'empreinte était là, et elle ne mesurait rien.

    Un exercice peut donc, à la place, déclarer « rendu » : ce qui est remis, et
    comment on le juge. C'est une porte étroite — il faut l'écrire, et le
    formateur y lit sa grille — et non l'absence de contrôle.
    """
    defauts = []
    for _module, e in _exercices(modules):
        renvoi = e.get("reponse")
        if e["guidage"] == "demonstration":
            continue  # une démonstration se lit, elle n'attend pas de réponse
        if not renvoi:
            rendu = (e.get("rendu") or "").strip()
            if len(rendu) < 40:
                defauts.append(
                    f"{e['id']} : ni renvoi « reponse », ni « rendu » décrivant "
                    "ce qui est remis et comment il est jugé"
                )
            continue
        if isinstance(renvoi, dict) and "valeur" in renvoi:
            defauts.append(f"{e['id']} : contient une valeur en dur — interdit")
            continue
        cle = f"{renvoi.get('scenario')}.{renvoi.get('cle')}"
        if cle not in reponses:
            defauts.append(f"{e['id']} : renvoi « {cle} » absent du manifeste")
    assert not defauts, "renvois de réponse :\n  " + "\n  ".join(defauts)


def test_aucune_reponse_attendue_ecrite_en_clair(modules, manifeste):
    """La règle qui prime : un exercice dont la réponse est trouvable sans le
    faire est un défaut (charte §3).

    Les valeurs que la fiche de contexte publie déjà — serveurs critiques,
    comptes de service, adresse du scanner autorisé — ne sont pas des fuites :
    SPEC §5.4 impose de les publier, et elles s'y perdent parmi leurs
    semblables. La règle et son exception vivent dans outils/fuites.py, partagé
    avec le constructeur du guide.
    """
    fuites = []
    for m in modules:
        texte = m["chemin"].read_text(encoding="utf-8")
        for fuite in chercher_fuites(texte, manifeste):
            fuites.append(f"{m['chemin'].name} : {fuite}")
    assert not fuites, "réponses écrites en clair :\n  " + "\n  ".join(fuites)


def test_aucune_date_absolue(modules):
    """Les données sont en fenêtre glissante : une date absolue serait fausse demain."""
    motif = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b")
    fuites = []
    for m in modules:
        for numero, ligne in enumerate(m["chemin"].read_text(encoding="utf-8").split("\n"), 1):
            if motif.search(ligne) and "doc:" not in ligne and "http" not in ligne:
                fuites.append(f"{m['chemin'].name}:{numero} : {ligne.strip()[:80]}")
    assert not fuites, "dates absolues :\n  " + "\n  ".join(fuites)


def test_lignes_de_moins_de_80_caracteres(modules):
    """SPEC §7.3 : lignes de moins de 80 caractères.

    Les tableaux Markdown et les URL sont dispensés : les couper les casserait.
    """
    longues = []
    for m in modules:
        dans_code = False
        for numero, ligne in enumerate(m["chemin"].read_text(encoding="utf-8").split("\n"), 1):
            if ligne.startswith("```"):
                dans_code = not dans_code
            if dans_code or ligne.lstrip().startswith("|") or "http" in ligne:
                continue
            if len(ligne) > 80:
                longues.append(f"{m['chemin'].name}:{numero} ({len(ligne)} car.)")
    assert not longues, f"{len(longues)} ligne(s) trop longues :\n  " + "\n  ".join(longues[:15])


# --------------------------------------------------------------------------
# Les pièges
# --------------------------------------------------------------------------

def test_chaque_piege_est_provoque_par_un_exercice(modules, pieges_lab):
    """SPEC §6.3 : chaque piège est provoqué volontairement dans un exercice."""
    provoques = {e.get("piege") for _, e in _exercices(modules) if e.get("piege")}
    attendus = {p["id"] for p in pieges_lab["pieges"]}
    manquants = attendus - provoques
    assert not manquants, f"pièges jamais provoqués : {sorted(manquants)}"
    inconnus = provoques - attendus
    assert not inconnus, f"pièges cités mais absents de docs/pieges-lab.json : {sorted(inconnus)}"


def test_les_pieges_sont_decrits_comme_ils_se_comportent(modules, pieges_lab):
    """On n'écrit pas ce que le piège est censé produire, mais ce qu'il produit.

    Constaté en lab : « [1025 TO *] » affiche une erreur, alors que
    « _exists_:champ » ne dit rien et renvoie zéro. Un module qui annonce un
    « échec silencieux » pour le premier serait faux.
    """
    par_id = {p["id"]: p for p in pieges_lab["pieges"]}
    defauts = []
    for module in modules:
        for _, e in _exercices([module]):
            identifiant = e.get("piege")
            if not identifiant:
                continue
            piege = par_id[identifiant]
            if piege.get("type") != "requete":
                continue  # un piège de plage de temps n'affiche pas de message
            muet = piege["ce_qui_echoue"]["message_affiche"] is None
            bloc = (e.get("solution", "") + " " + " ".join(e.get("erreurs_typiques") or [])).lower()
            if not muet and ("silencieu" in bloc or "sans message" in bloc or "muet" in bloc):
                defauts.append(
                    f"{e['id']} présente « {identifiant} » comme silencieux, or Kibana affiche "
                    f"« {piege['ce_qui_echoue']['message_affiche']} »"
                )
            annonce_erreur = (
                "erreur" in bloc
                and "aucune erreur" not in bloc
                and "sans erreur" not in bloc
            )
            if muet and annonce_erreur:
                defauts.append(
                    f"{e['id']} présente « {identifiant} » comme une erreur, or il ne dit rien"
                )
    assert not defauts, "pièges mal décrits :\n  " + "\n  ".join(defauts)


# --------------------------------------------------------------------------
# Contrôles contre le lab
# --------------------------------------------------------------------------

def test_les_libelles_cites_existent_dans_l_interface(modules, kbn, config, lab_demarre):
    """Un libellé d'interface ne se traduit pas de tête (CLAUDE.md).

    Le contrôle se fait sur les traductions réellement servies par le lab dans
    la locale de kit.config.yaml.

    La liste des exceptions est celle d'outils/libelles.py, et elle est NOMMÉE :
    chaque entrée dit ce qu'elle désigne. Une liste d'exceptions large rendrait
    ce contrôle décoratif — c'est ce qui s'était produit, « Lens » et « Stack
    Management » y figurant en bloc alors qu'aucun des deux n'est affiché ainsi
    dans cette version.
    """
    locale = str(config.valeur("kibana.locale"))
    r = kbn.get(f"{kbn.base}/translations/{locale}.json", timeout=90)
    assert r.status_code == 200, f"traductions {locale} indisponibles (HTTP {r.status_code})"
    messages = r.json().get("messages", {})
    connus = set()
    for valeur in messages.values():
        texte = valeur.get("text") if isinstance(valeur, dict) else valeur
        if isinstance(texte, str) and texte:
            connus.add(normaliser_libelle(texte))

    assumes = {normaliser_libelle(x) for x in ANGLAIS_ASSUME}
    inconnus = []
    for _module, e in _exercices(modules):
        for libelle in e.get("libelles_ui") or []:
            forme = normaliser_libelle(libelle)
            if forme in connus or forme in assumes:
                continue
            inconnus.append(f"{e['id']} : « {libelle} »")
    assert not inconnus, (
        "libellés introuvables dans l'interface fr-FR du lab :\n  " + "\n  ".join(inconnus)
    )


def test_les_exceptions_de_libelles_sont_encore_en_anglais(kbn, config, lab_demarre):
    """L'inverse du contrôle précédent, et il compte autant.

    ANGLAIS_ASSUME liste les entrées que Kibana 9.5.3 laisse en anglais. Si une
    version ultérieure les traduit, le guide se mettra à citer un intitulé qui
    n'est plus à l'écran — sans que rien n'échoue. Ce test le fait échouer.
    """
    locale = str(config.valeur("kibana.locale"))
    r = kbn.get(f"{kbn.base}/translations/{locale}.json", timeout=90)
    assert r.status_code == 200
    connus = set()
    for valeur in r.json().get("messages", {}).values():
        texte = valeur.get("text") if isinstance(valeur, dict) else valeur
        if isinstance(texte, str) and texte:
            connus.add(normaliser_libelle(texte))

    traduits = [
        f"« {libelle} » ({role})"
        for libelle, role in ANGLAIS_ASSUME.items()
        if normaliser_libelle(libelle) in connus
    ]
    assert not traduits, (
        "ces libellés sont désormais traduits : retirez-les d'ANGLAIS_ASSUME et "
        "reprenez le parcours qui les cite en anglais :\n  " + "\n  ".join(traduits)
    )


def test_les_requetes_kql_donnent_ce_qui_est_annonce(modules, reponses, lab_demarre):
    """Chaque requête KQL du parcours est tapée dans Discover (SPEC §10)."""
    a_jouer = [
        (e["id"], requete)
        for _, e in _exercices(modules)
        for requete in (e.get("requetes_kql") or [])
    ]
    if not a_jouer:
        pytest.skip("NON EXÉCUTÉ : aucune requête KQL déclarée dans le parcours")

    defauts = []
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        K.ouvrir_discover(page)
        for identifiant, requete in a_jouer:
            kql = requete["kql"]
            attendu = requete.get("attendu", "non_vide")
            obtenu = K.compter_avec_kql(page, kql)

            if attendu == "non_vide":
                if not obtenu:
                    defauts.append(f"{identifiant} : « {kql} » renvoie {obtenu}, attendu non vide")
            elif attendu == "vide":
                if obtenu != 0:
                    defauts.append(f"{identifiant} : « {kql} » renvoie {obtenu}, attendu 0")
            elif str(attendu).startswith("manifeste:"):
                cle = str(attendu).split(":", 1)[1]
                assert cle in reponses, f"{identifiant} : renvoi « {cle} » inconnu"
                cible = int(reponses[cle]["valeur"])
                if obtenu != cible:
                    defauts.append(
                        f"{identifiant} : « {kql} » renvoie {obtenu}, "
                        f"le manifeste dit {cible} ({cle})"
                    )
            else:
                defauts.append(f"{identifiant} : « attendu » inconnu — {attendu!r}")

    assert not defauts, "requêtes KQL :\n  " + "\n  ".join(defauts)


def test_le_corrige_du_formateur_couvre_toutes_les_questions(config):
    """Le formateur doit pouvoir corriger en salle CHAQUE question posée.

    Le corrigé s'était arrêté à Q15 quand le quiz est passé à 17 : les deux
    questions manquantes étaient précisément celles ajoutées pour couvrir deux
    pièges, et le formateur ne pouvait pas les corriger. Rien ne le signalait,
    puisque rien ne comparait les deux fichiers.
    """
    quiz_chemin = config.RACINE / "formateur" / "quiz.yaml"
    guide_chemin = config.RACINE / "formateur" / "guide-formateur.md"
    if not quiz_chemin.exists() or not guide_chemin.exists():
        pytest.skip("NON EXÉCUTÉ : quiz.yaml ou guide-formateur.md absent.")

    quiz = yaml.safe_load(quiz_chemin.read_text(encoding="utf-8")) or []
    posees = [q["id"] for q in quiz]
    guide = guide_chemin.read_text(encoding="utf-8")
    corrigees = set(re.findall(r"^\|\s*(Q\d+)\s*\|", guide, re.M))

    manquantes = [q for q in posees if q not in corrigees]
    assert not manquantes, (
        f"questions posées mais absentes du corrigé du formateur : {manquantes}"
    )

    fantomes = sorted(corrigees - set(posees))
    assert not fantomes, (
        f"corrigé pour des questions qui ne sont plus posées : {fantomes}"
    )

    # Le guide annonce aussi le nombre de questions : il doit dire la vérité.
    annonces = re.findall(r"(\d+)\s+questions", guide)
    faux = [n for n in annonces if int(n) != len(posees)]
    assert not faux, (
        f"le guide du formateur annonce {faux} question(s) alors que le quiz en "
        f"pose {len(posees)}"
    )


def test_le_tableau_des_types_de_M1_dit_ce_que_le_lab_montre(config):
    """Le tableau « ce que chaque forme suppose du champ » vient du lab, pas de mémoire.

    Il a longtemps écrit « joker sur le début : tout sauf un champ de type ip ».
    C'est faux, et d'une façon coûteuse : Elasticsearch refuse le joker de début
    sur tout ce qui n'est ni keyword, ni text, ni wildcard. Un analyste qui tape
    « destination.port : 44* » reçoit le même échec que sur une adresse, après
    qu'un tableau de référence lui a promis que seul le type ip posait problème.

    Les sondes de « lab/sonder_pieges.py » relèvent le comportement réel, forme
    par forme et type par type. Ce contrôle exige que le tableau les suive.
    """
    releve = config.RACINE / "docs" / "pieges-lab.json"
    module = config.RACINE / "parcours" / "M1.md"
    if not releve.exists() or not module.exists():
        pytest.skip("NON EXÉCUTÉ : docs/pieges-lab.json ou parcours/M1.md absent.")

    sondes = json.loads(releve.read_text(encoding="utf-8")).get("sondes_de_type")
    if not sondes:
        pytest.skip(
            "NON EXÉCUTÉ : docs/pieges-lab.json ne porte pas de « sondes_de_type ». "
            "Relancez « .venv/bin/python lab/sonder_pieges.py »."
        )

    texte = module.read_text(encoding="utf-8")
    ligne = next(
        (r for r in texte.splitlines() if r.startswith("| joker sur le début")), None
    )
    assert ligne, "le tableau des types de M1 n'a plus de ligne « joker sur le début »"

    # Le tableau parle français ; les sondes parlent le vocabulaire d'Elasticsearch.
    NOM_FR = {"long": "nombre", "date": "date", "ip": "adresse", "keyword": "keyword"}
    manques, faux = [], []
    for sonde in sondes:
        if sonde.get("forme") != "joker":
            continue
        mot = NOM_FR.get(sonde.get("type_de_champ", ""))
        if not mot:
            continue
        refuse = not sonde.get("aboutit", True) or sonde.get("message_affiche")
        present = mot in ligne.lower()
        if refuse and not present:
            manques.append(f"{sonde['type_de_champ']} (« {sonde['requete']} » a échoué en lab)")
        if not refuse and mot != "keyword" and present:
            faux.append(f"{sonde['type_de_champ']} (« {sonde['requete']} » a abouti en lab)")

    assert not manques, (
        "le tableau des types de M1 ne signale pas des types que le lab refuse : "
        + ", ".join(manques)
        + f"\n  ligne : {ligne}"
    )
    assert not faux, (
        "le tableau des types de M1 annonce refusés des types qui aboutissent : "
        + ", ".join(faux)
        + f"\n  ligne : {ligne}"
    )


def test_les_bonnes_reponses_du_quiz_ne_sont_pas_toujours_au_meme_rang(config):
    """Un quiz se triche au rang, pas au fond.

    À la première rédaction, la bonne réponse occupait le rang 2 pour treize
    questions sur dix-sept et le rang 3 pour les quatre autres : jamais la
    première ni la dernière. Un stagiaire qui cochait systématiquement la
    deuxième proposition obtenait 13/17, soit 76 %, sans avoir ouvert Kibana.
    Rien ne mesurait le fond ; l'évaluation mesurait un réflexe.

    Le contrôle exige donc que chaque rang soit correct au moins une fois, et
    qu'aucun ne dépasse le tiers des questions. Quatre propositions donnent
    25 % au hasard pur : tant que le meilleur rang reste sous le tiers, le
    cocher systématiquement ne rapporte pas sensiblement plus que le hasard,
    et ne remplace jamais la lecture de la question.
    """
    chemin = config.RACINE / "formateur" / "quiz.yaml"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : formateur/quiz.yaml absent.")

    quiz = yaml.safe_load(chemin.read_text(encoding="utf-8")) or []
    assert quiz, "quiz.yaml ne contient aucune question"

    nb_propositions = {len(q["propositions"]) for q in quiz}
    assert nb_propositions == {4}, (
        f"toutes les questions n'offrent pas quatre propositions : {sorted(nb_propositions)}"
    )

    rangs = [q["reponse"] for q in quiz]
    hors_bornes = [q["id"] for q in quiz if not 0 <= q["reponse"] < len(q["propositions"])]
    assert not hors_bornes, f"« reponse » hors des propositions : {hors_bornes}"

    compte = collections.Counter(rangs)
    repartition = ", ".join(f"rang {r} : {compte.get(r, 0)}" for r in range(4))

    vides = [r for r in range(4) if compte.get(r, 0) < 1]
    assert not vides, (
        f"rang(s) jamais correct(s) : {vides} — {repartition}. Un stagiaire qui "
        "repère un rang délaissé élimine gratuitement une proposition sur "
        "chaque question."
    )

    # Cocher toujours le même rang doit rester loin du hasard utile : au plus
    # le tiers des points, alors que quatre propositions en donnent un quart
    # au hasard pur. Au-delà, le rang devient une stratégie payante.
    meilleur = max(compte.values())
    assert meilleur / len(quiz) <= PART_MAXIMALE_D_UN_RANG, (
        f"cocher toujours le même rang rapporte {meilleur}/{len(quiz)} = "
        f"{meilleur / len(quiz):.0%}, au-delà des "
        f"{PART_MAXIMALE_D_UN_RANG:.0%} tolérés — {repartition}"
    )


def test_aucun_exercice_ne_valide_l_empreinte_d_un_autre(modules, manifeste):
    """Deux clés différentes peuvent porter la MÊME valeur — donc la même empreinte.

    Le contrôle voisin compare les clés, et c'est par là que le capstone a fui.
    R.source_la_moins_volumineuse valait « ids.alert » et S5.source aussi ;
    R.source_ports_hauts valait « firewall.traffic » et S6.source aussi. Deux
    clés distinctes, deux exercices distincts, une seule empreinte : le
    stagiaire validait M4-E7 avec ce qu'il avait relevé à M2-E5, et M4-E8 avec
    ce qu'il avait relevé à M1-E5. Le capstone n'évaluait plus rien.

    On compare donc les EMPREINTES, qui sont ce que le guide vérifie
    réellement. Un réemploi assumé de la même clé reste permis — le contrôle
    voisin exige alors qu'il soit annoncé. Ce qui est refusé ici, c'est la
    collision entre deux clés différentes.
    """
    par_cle = {}
    for bloc in [manifeste.get("reperes"), *manifeste["scenarios"]]:
        if not bloc:
            continue
        for reponse in bloc["reponses"]:
            par_cle[f"{bloc['id']}.{reponse['cle']}"] = tuple(reponse.get("empreintes") or ())

    empreinte_vers_cles = {}
    for cle, empreintes in par_cle.items():
        for e in empreintes:
            empreinte_vers_cles.setdefault(e, set()).add(cle)

    employees = {}
    for _module, exercice in _exercices(modules):
        renvoi = exercice.get("reponse")
        if not renvoi:
            continue
        employees.setdefault(f"{renvoi['scenario']}.{renvoi['cle']}", []).append(exercice["id"])

    collisions = []
    for empreinte, cles in empreinte_vers_cles.items():
        notees = sorted(c for c in cles if c in employees)
        if len(notees) > 1:
            detail = " ; ".join(f"{c} ({', '.join(employees[c])})" for c in notees)
            collisions.append(f"empreinte {empreinte[:16]}… partagée par {detail}")

    assert not collisions, (
        "des exercices se valident avec la même empreinte sous des clés "
        "différentes :\n  " + "\n  ".join(collisions)
    )


def test_tout_reemploi_de_reponse_est_annonce(modules):
    """Une réponse déjà rendue doit être présentée comme un contrôle, pas comme
    une découverte.

    Trente exercices se partagent dix-neuf réponses. Les répétitions sont
    voulues — vérifier qu'un écran rejoué par API montre la même chose, qu'un
    second Space voit le même parc, qu'un clic pose bien le filtre attendu —
    mais muettes, elles se lisent comme un oubli, et le stagiaire retape de
    mémoire au lieu de refaire le geste. Chaque réemploi doit donc le dire.

    L'annonce est acceptée dans la DÉMARCHE — lue après avoir répondu — ou dans
    le CONTEXTE, lu avant. M2-E2 emploie la seconde place (« Vous avez déjà
    répondu à la requête au module précédent ») et c'est sans doute la
    meilleure : prévenir avant évite au stagiaire de croire à une question
    piège. Les deux conviennent ; ne rien dire, non.
    """
    marqueurs = (
        "déjà", "deja", "connaiss", "même réponse", "meme reponse",
        "module m", "relevé au module", "celle du module", "celui du module",
        "c'est voulu", "est le contrôle", "est le controle",
    )
    vus: dict[str, str] = {}
    defauts = []
    for _module, e in _exercices(modules):
        renvoi = e.get("reponse")
        if not renvoi:
            continue
        cle = f"{renvoi['scenario']}.{renvoi['cle']}"
        if cle not in vus:
            vus[cle] = e["id"]
            continue
        annonce = ((e.get("solution") or "") + " " + (e.get("contexte") or "")).lower()
        if not any(m in annonce for m in marqueurs):
            defauts.append(
                f"{e['id']} rend la même réponse que {vus[cle]} ({cle}) "
                "sans l'annoncer dans sa démarche"
            )
    assert not defauts, (
        "réemplois de réponse non annoncés :\n  " + "\n  ".join(defauts)
    )
