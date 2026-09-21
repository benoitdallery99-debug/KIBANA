"""verif-parcours — ce que prouve cette suite (SPEC §10) :

chaque réponse attendue vient du manifeste et n'est jamais écrite en clair ;
chaque requête KQL du parcours, tapée dans Discover, renvoie ce qui est annoncé ;
chaque libellé d'interface cité existe dans l'interface fr-FR du lab ;
chaque piège de SPEC §6.3 est provoqué par un exercice ; le guidage est dégressif.
"""

from __future__ import annotations

import json
import re

import pytest
import yaml

from outils.fuites import chercher as chercher_fuites
from verif.e2e import kibana as K

pytestmark = pytest.mark.parcours

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
def manifeste(config):
    chemin = config.RACINE / "data" / "manifest.json"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : data/manifest.json absent. Lancez « make data ».")
    return json.loads(chemin.read_text(encoding="utf-8"))


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


def test_durees_coherentes(modules):
    """La somme des exercices doit tenir dans la durée annoncée du module."""
    defauts = []
    total = 0
    for m in modules:
        annonce = m["entete"]["duree_minutes"]
        total += annonce
        somme = sum(e.get("duree_minutes", 0) for e in m["entete"]["exercices"])
        if somme > annonce:
            defauts.append(
                f"{m['entete']['id']} : {somme} min d'exercices "
                f"pour {annonce} annoncées"
            )
    assert not defauts, "durées :\n  " + "\n  ".join(defauts)
    assert 300 <= total <= 400, f"parcours de {total} min, 6 h visées (SPEC §1)"


# --------------------------------------------------------------------------
# Les réponses viennent du manifeste, et n'apparaissent jamais en clair
# --------------------------------------------------------------------------

def test_chaque_exercice_renvoie_a_une_reponse_du_manifeste(modules, reponses):
    defauts = []
    for _module, e in _exercices(modules):
        renvoi = e.get("reponse")
        if e["guidage"] == "demonstration":
            continue  # une démonstration se lit, elle n'attend pas de réponse
        if not renvoi:
            defauts.append(f"{e['id']} : aucun renvoi « reponse »")
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
    """
    locale = str(config.valeur("kibana.locale"))
    r = kbn.get(f"{kbn.base}/translations/{locale}.json", timeout=90)
    assert r.status_code == 200, f"traductions {locale} indisponibles (HTTP {r.status_code})"
    messages = r.json().get("messages", {})
    connus = set()
    for valeur in messages.values():
        texte = valeur.get("text") if isinstance(valeur, dict) else valeur
        if isinstance(texte, str):
            connus.add(texte.strip())
    # Les noms propres de l'interface ne sont pas traduits : ils n'apparaissent
    # donc pas dans le fichier de traduction, et sont admis tels quels.
    NON_TRADUITS = {
        "Discover", "Lens", "Kibana", "Elasticsearch", "KQL", "Lucene", "ES|QL",
        "Elastic", "Maps", "Canvas", "Management", "Stack Management",
    }
    inconnus = []
    for _module, e in _exercices(modules):
        for libelle in e.get("libelles_ui") or []:
            if libelle in NON_TRADUITS or libelle in connus:
                continue
            inconnus.append(f"{e['id']} : « {libelle} »")
    assert not inconnus, (
        "libellés introuvables dans l'interface fr-FR du lab :\n  " + "\n  ".join(inconnus)
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
