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

# Les bornes du parcours ne sont plus écrites ici : elles viennent de
# kit.config.yaml, « seule source de vérité » (CLAUDE.md). Le fichier y portait
# « duree_cible_heures: 6 », que RIEN ne lisait et qui était faux de trois
# quarts d'heure — un paramètre décoratif dans le fichier même qui interdit les
# valeurs en dur. SPEC §1 ne budgétait ni la lecture des corps de module ni le
# rappel actif, que docs/CHARTE_REDACTION.md impose (écart E10 de
# docs/JOURNAL.md) ; le kit garde son contenu et dit la durée qu'il tient.


def _minutes_de_lecture(corps: str) -> int:
    """Temps de lecture du corps d'un module, arrondi à la minute supérieure."""
    return math.ceil(len(corps.split()) / MOTS_PAR_MINUTE)


def test_durees_coherentes(modules, config):
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
    cible = float(config.valeur("formation.duree_cible_heures")) * 60
    marge = float(config.valeur("formation.duree_tolerance_minutes"))
    bas, haut = cible - marge, cible + marge
    assert bas <= total <= haut, (
        f"parcours de {total} min, hors des bornes {bas:.0f}-{haut:.0f} que "
        f"kit.config.yaml fixe ({cible:.0f} min ± {marge:.0f}) :\n  "
        + "\n  ".join(detail)
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


@pytest.fixture(scope="module")
def catalogue_libelles(kbn, config, lab_demarre):
    """Les textes servis par le lab dans la locale du kit."""
    locale = str(config.valeur("kibana.locale"))
    r = kbn.get(f"{kbn.base}/translations/{locale}.json", timeout=90)
    if r.status_code != 200:
        return set()
    textes = set()
    for valeur in r.json().get("messages", {}).values():
        texte = valeur.get("text") if isinstance(valeur, dict) else valeur
        if isinstance(texte, str) and texte:
            textes.add(texte)
    return textes


def test_aucun_libelle_cite_avec_une_apostrophe_droite(modules, catalogue_libelles):
    """L'apostrophe d'un libellé se recopie, elle ne se retape pas.

    Le catalogue fr-FR sert « Impossible d’extraire les résultats de recherche »
    avec l'apostrophe typographique sous la clé du bandeau d'erreur — celui que
    le stagiaire obtient — et la même phrase avec l'apostrophe droite sous trois
    autres clés, d'autres composants. Une citation écrite à la main avec
    l'apostrophe droite passait donc le contrôle d'existence : elle existe, mais
    pas là où le parcours la montre.

    Ce contrôle refuse une citation à l'apostrophe droite dès lors que le
    catalogue en sert la variante typographique. C'est étroit, et c'est voulu :
    on ne devine pas quelle clé i18n le parcours vise, on refuse seulement de
    laisser passer la forme que le lab n'affiche pas à cet endroit.
    """
    if not catalogue_libelles:
        pytest.skip("NON EXÉCUTÉ : catalogue de libellés indisponible.")

    typographiques = {
        libelle for libelle in catalogue_libelles if "\u2019" in libelle
    }
    equivalents = {t.replace("\u2019", "'"): t for t in typographiques}

    defauts = []
    for _module, exercice in _exercices(modules):
        for libelle in exercice.get("libelles_ui") or []:
            if "'" in libelle and libelle in equivalents:
                defauts.append(
                    f"{exercice['id']} : « {libelle} » — le lab sert « "
                    f"{equivalents[libelle]} », avec l'apostrophe typographique"
                )
    assert not defauts, (
        "libellés cités avec l'apostrophe droite alors que le lab en sert la "
        "forme typographique :\n  " + "\n  ".join(defauts)
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


# --------------------------------------------------------------------------
# ES|QL
# --------------------------------------------------------------------------

_BLOC_ESQL = re.compile(r"```esql\n(.*?)```", re.S)

# Seuil de précision par défaut de l'agrégation « cardinality », annoncé par le
# corps de M2. En deçà, COUNT_DISTINCT est exact ; au-delà, c'est une estimation.
SEUIL_DE_PRECISION_PAR_DEFAUT = 3000


def _requetes_esql(modules):
    """(module, numéro de ligne, requête) pour chaque bloc ```esql du parcours."""
    trouvees = []
    for module in modules:
        texte = module["chemin"].read_text(encoding="utf-8")
        for bloc in _BLOC_ESQL.finditer(texte):
            ligne = texte.count("\n", 0, bloc.start()) + 1
            trouvees.append((module["chemin"].name, ligne, bloc.group(1).strip()))
    return trouvees


def _jouer_esql(es, requete: str):
    """Renvoie (colonnes, lignes) ou lève avec le message d'Elasticsearch."""
    r = es.post(
        f"{es.base}/_query",
        data=json.dumps({"query": requete}),
        timeout=120,
    )
    if r.status_code != 200:
        raise AssertionError(f"HTTP {r.status_code} — {r.text[:400]}")
    charge = r.json()
    return [c["name"] for c in charge.get("columns", [])], charge.get("values", [])


def test_chaque_requete_esql_du_parcours_repond_dans_le_lab(modules, lab_demarre, es):
    """Toute requête donnée au stagiaire est rejouée, comme les requêtes KQL.

    ÉCART CORRIGÉ : « requetes_kql » couvrait les requêtes portées par les
    exercices, mais les quatre requêtes ES|QL du corps de M2 n'étaient rejouées
    par rien. Elles sont pourtant copiées telles quelles par le stagiaire : une
    faute de syntaxe, un champ disparu du jeu, une fonction retirée par une
    montée de version, et le module fait taper une requête qui échoue — sans
    que rien du kit ne le signale. La charte l'interdit ; ce test l'applique.
    """
    a_jouer = _requetes_esql(modules)
    if not a_jouer:
        pytest.skip("NON EXÉCUTÉ : aucun bloc ```esql dans le parcours")

    defauts = []
    for fichier, ligne, requete in a_jouer:
        repere = f"{fichier}:{ligne}"
        try:
            colonnes, lignes = _jouer_esql(es, requete)
        except AssertionError as exc:
            defauts.append(f"{repere} : {exc}\n      {requete.splitlines()[0]}")
            continue
        if not colonnes:
            defauts.append(f"{repere} : aucune colonne renvoyée")
        if not lignes:
            defauts.append(
                f"{repere} : zéro ligne — le stagiaire verrait un tableau vide\n"
                f"      {requete.splitlines()[0]}"
            )

    assert not defauts, (
        f"{len(defauts)} requête(s) ES|QL du parcours ne répondent pas :\n  "
        + "\n  ".join(defauts)
    )


def test_le_contraste_de_cardinalite_promis_par_M2_existe_dans_le_lab(
    modules, lab_demarre, es
):
    """M2 promet « voir l'écart de vos yeux » : encore faut-il qu'il y ait un écart.

    Le module fait taper deux fois COUNT_DISTINCT sur le même champ, une fois au
    seuil par défaut, une fois à 40 000, et annonce que les deux nombres
    diffèrent parce que le champ porte plus de 3 000 valeurs distinctes. Si le
    générateur venait à produire moins de domaines, les deux requêtes rendraient
    le même chiffre : la démonstration ne montrerait plus rien, et le stagiaire
    conclurait que l'approximation est un mythe. Rien ne le signalait.
    """
    paires = {}
    for fichier, ligne, requete in _requetes_esql(modules):
        m = re.search(r"COUNT_DISTINCT\(\s*([\w.]+)\s*(?:,\s*(\d+)\s*)?\)", requete)
        if not m:
            continue
        paires.setdefault(m.group(1), {})[m.group(2) or "defaut"] = (
            f"{fichier}:{ligne}",
            requete,
        )

    contrastes = {c: v for c, v in paires.items() if len(v) >= 2}
    if not contrastes:
        pytest.skip(
            "NON EXÉCUTÉ : aucun champ n'est compté deux fois avec deux seuils "
            "de précision dans le parcours"
        )

    defauts = []
    for champ, seuils in contrastes.items():
        mesures = {}
        for seuil, (repere, requete) in seuils.items():
            _, lignes = _jouer_esql(es, requete)
            mesures[seuil] = (int(lignes[0][0]), repere)

        exact = max(v for v, _ in mesures.values())
        if exact <= SEUIL_DE_PRECISION_PAR_DEFAUT:
            defauts.append(
                f"{champ} : {exact} valeurs distinctes, sous le seuil de "
                f"{SEUIL_DE_PRECISION_PAR_DEFAUT} — les deux requêtes de M2 "
                f"rendront le même nombre et la leçon tombe à plat"
            )
            continue
        distincts = {v for v, _ in mesures.values()}
        if len(distincts) < 2:
            defauts.append(
                f"{champ} : les deux seuils rendent {distincts.pop()} — "
                f"aucun écart à montrer ({', '.join(r for _, r in mesures.values())})"
            )

    assert not defauts, "contraste de cardinalité :\n  " + "\n  ".join(defauts)


# --------------------------------------------------------------------------
# Vocabulaire de la charte
# --------------------------------------------------------------------------

# La fenêtre du sélecteur de temps s'écrit « plage de temps » partout
# (docs/CHARTE_REDACTION.md §2). L'interface n'offrant aucun libellé unique à
# citer — relevé dans fr-FR de 9.5.3 : « plage temporelle » 202 fois, « plage
# horaire » 12, « plage de temps » 11, et le sélecteur n'affiche que sa valeur —
# le kit en choisit un et s'y tient.
#
# Deux synonymes rôdaient. « période » neuf fois, dont deux dans M4 où le mot
# sert DÉJÀ à l'intervalle d'une balise. « plage temporelle » quatre fois hors
# citation — le reste des occurrences appartient à des libellés d'interface, qui
# se citent tels qu'ils s'affichent et ne peuvent donc pas être réécrits.
SYNONYMES_INTERDITS = {
    "période": (
        "période de la balise",   # l'intervalle d'une balise, autre notion
        "périodique",
    ),
    "plage temporelle": (         # fragments de libellés cités, intouchables
        "appliquer une plage temporelle personnalisée",
        "enregistrer la plage temporelle avec le tableau de bord",
        "enregistré la plage temporelle avec le tableau de bord",
        "enregistrez la plage temporelle avec le tableau de bord",
        "« plage temporelle »",
        "- plage temporelle",
    ),
}

FICHIERS_DU_STAGIAIRE = (
    "parcours/M0.md", "parcours/M1.md", "parcours/M2.md",
    "parcours/M3.md", "parcours/M4.md", "parcours/M5.md",
    "formateur/quiz.yaml", "formateur/matrice.md",
    "formateur/epreuve-pratique.md",
)


def test_un_seul_mot_pour_la_fenetre_de_temps(config):
    """Trois mots pour une même chose, dans un kit qui s'adresse à des débutants.

    Le stagiaire lisait « plage de temps » dans M0, « période » dans M1 et
    « plage temporelle » dans le quiz, pour le même sélecteur. Pire, M4
    employait « période » dans ses deux sens à trois exercices d'écart : la
    fenêtre d'observation, et l'intervalle entre deux requêtes d'une balise.
    Un lecteur qui doit deviner lequel des deux est en jeu ne lit plus, il
    interprète.

    Le contrôle porte sur le texte DÉPLIÉ, sans retours à la ligne : un libellé
    cité coupé en deux par le pliage à 80 colonnes doit rester reconnaissable,
    sans quoi le test refuserait ce que la charte exige de citer.
    """
    fautes = []
    for nom in FICHIERS_DU_STAGIAIRE:
        chemin = config.RACINE / nom
        if not chemin.exists():
            continue
        deplie = re.sub(r"\s+", " ", chemin.read_text(encoding="utf-8")).lower()
        for terme, permis in SYNONYMES_INTERDITS.items():
            for trouve in re.finditer(re.escape(terme), deplie):
                fenetre = deplie[max(0, trouve.start() - 90):trouve.end() + 90]
                if any(p in fenetre for p in permis):
                    continue
                extrait = deplie[max(0, trouve.start() - 45):trouve.end() + 45]
                fautes.append(f"{nom} « {terme} » — …{extrait}…")

    assert not fautes, (
        f"{len(fautes)} emploi(s) d'un synonyme de « plage de temps » :\n  "
        + "\n  ".join(fautes)
    )


# --------------------------------------------------------------------------
# Les horaires publiés au formateur
# --------------------------------------------------------------------------

def test_le_deroule_minute_tient_debout(modules, config):
    """Le déroulé du formateur est arithmétique : il doit tomber juste.

    Une minute ajoutée au corps de M3 a décalé tout l'après-midi de la formule
    B, et rien ne l'a vu : le tableau annonçait encore « 14 h 39 » pour un
    module qui commence à 14 h 40, et « 2 h 19 » pour deux modules qui en font
    2 h 20. Un formateur planifie sa journée là-dessus. On recalcule donc la
    ligne du temps : chaque heure de départ doit valoir la précédente plus sa
    durée, et la durée annoncée d'un module doit être celle qu'il déclare.
    """
    chemin = config.RACINE / "formateur" / "guide-formateur.md"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : formateur/guide-formateur.md absent.")
    texte = chemin.read_text(encoding="utf-8")

    duree = {m["entete"]["id"]: m["entete"]["duree_minutes"] for m in modules}

    lignes = re.findall(
        r"^\|\s*(\d{2})\s*h\s*(\d{2})\s*\|\s*(\d+)\s*min\s*\|\s*(.+?)\s*\|$",
        texte, re.M,
    )
    if len(lignes) < 5:
        pytest.skip("NON EXÉCUTÉ : pas de déroulé horaire reconnaissable.")

    defauts = []
    attendu = None
    for heures, minutes, mn, quoi in lignes:
        debut = int(heures) * 60 + int(minutes)
        if attendu is not None and debut != attendu:
            defauts.append(
                f"« {quoi[:44]} » commence à {heures} h {minutes}, "
                f"la ligne précédente le pose à {attendu // 60:02d} h {attendu % 60:02d}"
            )
        module = re.search(r"\*\*(M\d)\b", quoi)
        if module and module.group(1) in duree:
            if int(mn) != duree[module.group(1)]:
                defauts.append(
                    f"{module.group(1)} : {mn} min au déroulé, "
                    f"{duree[module.group(1)]} min déclarées par le module"
                )
        attendu = debut + int(mn)

    # Le total annoncé en tête du guide, et la somme des séances de la formule A.
    total = sum(duree.values())
    for annonce in re.findall(r"(\d) h (\d{2}) de parcours", texte) + \
            re.findall(r"vaut \*\*(\d) h (\d{2})\*\*", texte):
        publie = int(annonce[0]) * 60 + int(annonce[1])
        if publie != total:
            defauts.append(
                f"durée publiée {annonce[0]} h {annonce[1]} ({publie} min), "
                f"parcours réel {total} min"
            )

    assert not defauts, "déroulé minuté faux :\n  " + "\n  ".join(defauts)


def test_le_formateur_ne_propose_jamais_de_couper_un_evaluateur_unique(modules, config):
    """Couper un exercice unique évaluateur, c'est rendre un objectif non mesuré.

    Le guide du formateur disait les deux choses à trois lignes d'écart : « ne
    sacrifiez ni M2-E5 ni M5-E3, chacun est le SEUL à évaluer son objectif »,
    et, juste avant, « sacrifiez … la construction du second écran de M4-E2 » —
    or M4-E2 est le seul évaluateur de M4-O2. Le formateur pressé suivait la
    première phrase.

    On recalcule la couverture depuis le parcours : la liste protégée du guide
    doit être EXACTEMENT celle des exercices à évaluateur unique, et aucun
    d'eux ne doit figurer dans la phrase qui dit quoi sacrifier.
    """
    chemin = config.RACINE / "formateur" / "guide-formateur.md"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : formateur/guide-formateur.md absent.")
    texte = chemin.read_text(encoding="utf-8")

    couverture = collections.defaultdict(list)
    for m in modules:
        for exercice in m["entete"]["exercices"]:
            for objectif in exercice.get("objectifs", []):
                couverture[objectif].append(exercice["id"])
    uniques = {v[0] for v in couverture.values() if len(v) == 1}

    deplie = re.sub(r"\s+", " ", texte)

    defauts = []
    phrase = re.search(r"Si vous prenez du retard.*?\.", deplie)
    if phrase:
        for identifiant in sorted(uniques):
            if identifiant in phrase.group(0):
                defauts.append(
                    f"{identifiant} est proposé au sacrifice alors qu'il est le "
                    f"seul à évaluer son objectif"
                )

    annonce = re.search(r"ne se sacrifient à aucune heure.*?:\s*(.+?)\.", deplie)
    if not annonce:
        defauts.append("la liste des exercices à ne jamais sacrifier a disparu du guide")
    else:
        cites = set(re.findall(r"M\d-E\d+", annonce.group(1)))
        if cites != uniques:
            manquants = sorted(uniques - cites)
            en_trop = sorted(cites - uniques)
            if manquants:
                defauts.append(f"absents de la liste protégée : {', '.join(manquants)}")
            if en_trop:
                defauts.append(
                    f"protégés à tort (ils ne sont pas seuls évaluateurs) : "
                    f"{', '.join(en_trop)}"
                )

    assert not defauts, (
        "le guide du formateur se contredit sur ce qui peut être coupé :\n  "
        + "\n  ".join(defauts)
    )


# Les fichiers que le stagiaire et le formateur LISENT, par opposition aux
# documents de fabrication (journal, rapport de recette, relevé de capacités),
# qui datent volontairement leurs constats.
LUS_EN_SALLE = (
    "parcours/M0.md", "parcours/M1.md", "parcours/M2.md",
    "parcours/M3.md", "parcours/M4.md", "parcours/M5.md",
    "formateur/guide-formateur.md", "formateur/quiz.yaml",
    "formateur/matrice.md", "formateur/epreuve-pratique.md",
    "guide/fiche-memo.yaml", "guide/glossaire.yaml",
)


def test_aucune_version_en_dur_ne_diverge_de_la_configuration(config):
    """CLAUDE.md : « jamais de version, locale ou graine en dur ».

    Deux textes citent la version en toutes lettres — M0, qui explique que le
    panneau de navigation reste en anglais « en version 9.5.3 », et l'en-tête du
    guide du formateur. Le chiffre y a sa place : on parle d'un comportement
    propre à CETTE version. Ce qui manquait, c'est le lien : une montée de
    version aurait laissé les deux phrases parler d'une version que le kit ne
    livre plus, sans que rien n'échoue. Le contrôle exige donc que toute version
    citée soit celle de kit.config.yaml.
    """
    attendue = str(config.valeur("stack.version"))
    fautes = []
    for nom in LUS_EN_SALLE:
        chemin = config.RACINE / nom
        if not chemin.exists():
            continue
        texte = chemin.read_text(encoding="utf-8")
        for numero, ligne in enumerate(texte.split("\n"), 1):
            # Les lookarounds écartent les adresses IP : « 10.0.0.0/8 » porte
            # « 10.0.0 », qui n'est pas une version.
            for trouvee in re.findall(r"(?<![\d.])\d+\.\d+\.\d+(?![\d.])", ligne):
                if trouvee != attendue:
                    fautes.append(f"{nom}:{numero} cite {trouvee} — kit.config.yaml "
                                  f"dit {attendue}")
    assert not fautes, (
        "version citée hors configuration :\n  " + "\n  ".join(fautes)
    )


def test_les_indices_sont_a_deux_niveaux(modules):
    """SPEC §6.1 et la charte §5 : « indices à deux niveaux ».

    Le premier oriente, le second montre presque. Deux exercices en portaient
    trois et quatre — M0-E2 et M1-E5, celui-là parce que le passage au guidage
    semi-guidé y avait versé les clics retirés des consignes. Quatre indices, ce
    n'est plus une gradation : c'est la solution en pièces détachées, et le
    stagiaire qui ouvre le premier ouvre les quatre.

    Un exercice en DÉMONSTRATION montre déjà les gestes : il peut n'avoir aucun
    indice — c'est le cas de quatre d'entre eux — ou porter les deux niveaux
    quand ils apprennent autre chose que le geste, comme M5-E1. Ce qu'aucun
    exercice ne peut faire, c'est en porter un seul, ou plus de deux.
    """
    defauts = []
    for _, exercice in _exercices(modules):
        indices = exercice.get("indices") or []
        admis = (0, 2) if exercice.get("guidage") == "demonstration" else (2,)
        if len(indices) not in admis:
            defauts.append(
                f"{exercice['id']} ({exercice.get('guidage')}) : {len(indices)} "
                f"indice(s), {' ou '.join(str(a) for a in admis)} attendu(s)"
            )
    assert not defauts, "indices à deux niveaux :\n  " + "\n  ".join(defauts)


def test_aucune_requete_en_ligne_dans_le_corps_d_un_module(modules):
    """docs/CHARTE_REDACTION.md §8 : les requêtes vont dans un bloc de code.

    Trois requêtes traînaient dans une phrase de M1, guillemets français et
    astérisques échappées — « destination.port : 44\\* ». En ligne, une requête
    ne se copie pas d'un clic, son astérisque doit être protégée du Markdown, et
    rien ne dit au lecteur que c'est du KQL plutôt que de la prose. Le contrôle
    ne regarde que le CORPS : une consigne est du YAML, elle n'a pas de bloc à
    sa disposition et emploie l'italique de code.
    """
    motif = re.compile(r"[a-z_@]+\.[a-z_.]+\s*:\s*\S")
    fautes = []
    for module in modules:
        dans_un_bloc = False
        for numero, ligne in enumerate(module["corps"].split("\n"), 1):
            if ligne.startswith("```"):
                dans_un_bloc = not dans_un_bloc
                continue
            if dans_un_bloc:
                continue
            if motif.search(re.sub(r"`[^`]*`", "", ligne)):
                fautes.append(
                    f"{module['chemin'].name} (corps, ligne {numero}) : "
                    f"{ligne.strip()[:70]}"
                )
    assert not fautes, (
        "requêtes écrites en ligne dans un corps de module :\n  " + "\n  ".join(fautes)
    )


def test_explorer_dans_discover_n_est_jamais_annonce_dans_le_menu(modules, config):
    """Sondé en lab : cette action n'est PAS dans le menu « … » d'un panneau.

    Elle est dans la rangée de boutons qui apparaît au survol, en haut à droite
    — ni en lecture ni en modification le menu ne la propose
    (outils/sonde_explorer_discover.py, constat reporté au point Q de
    docs/capacites.md). Le parcours l'annonçait « dans le menu du panneau » à
    quatre endroits, et un stagiaire qui cherche au mauvais endroit conclut que
    la fonction n'existe pas — ou que son écran est cassé.
    """
    fautes = []
    fichiers = [m["chemin"] for m in modules]
    for nom in ("guide-formateur.md", "quiz.yaml", "epreuve-pratique.md"):
        chemin = config.RACINE / "formateur" / nom
        if chemin.exists():
            fichiers.append(chemin)

    for chemin in fichiers:
        deplie = re.sub(r"\s+", " ", chemin.read_text(encoding="utf-8"))
        for trouve in re.finditer(r"Explorer dans Discover", deplie):
            fenetre = deplie[max(0, trouve.start() - 160):trouve.end() + 160]
            if "menu du panneau" in fenetre or "menu « … »" in fenetre:
                # Dire « elle n'est PAS dans le menu » est l'énoncé juste : la
                # négation blanchit la phrase, où qu'elle tombe autour.
                if re.search(r"n'y est pas|jamais dans le menu|il n'y est jamais"
                             r"|ne le cherchez pas dans le menu"
                             r"|n'est \*\*pas dans le menu"
                             r"|PAS dans le menu", fenetre):
                    continue
                fautes.append(f"{chemin.name} : …{fenetre[100:260]}…")

    assert not fautes, (
        "« Explorer dans Discover » annoncée dans le menu du panneau :\n  "
        + "\n  ".join(fautes)
    )
