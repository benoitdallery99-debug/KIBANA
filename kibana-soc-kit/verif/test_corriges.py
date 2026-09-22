"""verif-corriges — ce que prouve cette suite (SPEC §10) :

import des tableaux de bord dans un Space VIERGE sans erreur ni référence
manquante, rendu de chaque panneau sans erreur, et valeurs affichées égales à
ce que renvoie Elasticsearch pour la même question.
"""

from __future__ import annotations

import json
import re

import pytest

from verif.e2e import kibana as K

pytestmark = pytest.mark.corriges

ESPACE_ESSAI = "verif-corriges-vierge"
# Les corrigés sont chargés hors du Space de formation (leurs titres donnent
# les réponses de M3 et M4) : les tests vont les lire là où ils vivent.
ESPACE_CORRIGES = "corriges"
TABLEAUX = ("kit-soc-sante-collecte", "kit-soc-vue-ids")


@pytest.fixture(scope="module")
def ndjson(config):
    chemin = config.RACINE / "corriges" / "tableaux-de-bord.ndjson"
    if not chemin.exists():
        pytest.skip(
            "NON EXÉCUTÉ : corriges/tableaux-de-bord.ndjson absent. "
            "Lancez « .venv/bin/python corriges/construire.py »."
        )
    return chemin


@pytest.fixture(scope="module")
def space_vierge(kbn, lab_demarre):
    """Un Space neuf, pour prouver que l'import ne dépend de rien de préexistant."""
    kbn.delete(f"{kbn.base}/api/spaces/space/{ESPACE_ESSAI}", timeout=60)
    r = kbn.post(f"{kbn.base}/api/spaces/space", timeout=60, json={
        "id": ESPACE_ESSAI,
        "name": "Vérification — Space vierge",
        "description": "Créé et supprimé par verif-corriges.",
        "solution": "classic",
    })
    assert r.status_code == 200, f"création du Space d'essai : HTTP {r.status_code} {r.text[:200]}"
    yield ESPACE_ESSAI
    kbn.delete(f"{kbn.base}/api/spaces/space/{ESPACE_ESSAI}", timeout=60)


@pytest.fixture(scope="module")
def import_realise(kbn, ndjson, space_vierge):
    """Importe les corrigés dans le Space vierge et rend le résultat de l'import.

    Comportement relevé en lab, qui surprend et que le module M5 enseigne : un
    tableau de bord est un objet PARTAGEABLE entre Spaces. Quand l'identifiant
    importé existe déjà dans un autre Space, Kibana ne l'écrase pas et n'échoue
    pas : il crée une COPIE sous un nouvel identifiant, rendu dans
    « destinationId » — et ce, même avec « createNewCopies=false ».
    Les contrôles suivent donc ce que l'import déclare avoir créé.
    """
    with ndjson.open("rb") as f:
        r = kbn.post(
            f"{kbn.base}/s/{space_vierge}/api/saved_objects/_import?createNewCopies=false",
            files={"file": ("tableaux-de-bord.ndjson", f, "application/ndjson")},
            # Content-Type à None : la session porte « application/json » par
            # défaut, ce qui empêcherait requests de poser la frontière
            # multipart et ferait répondre 415 (constaté en lab).
            headers={"kbn-xsrf": "true", "Content-Type": None},
            timeout=180,
        )
    assert r.status_code == 200, f"import : HTTP {r.status_code} {r.text[:400]}"
    resultat = r.json()
    # Identifiant d'origine → identifiant réellement créé dans ce Space.
    resultat["_correspondance"] = {
        o["id"]: o.get("destinationId", o["id"]) for o in resultat.get("successResults", [])
    }
    return resultat


def test_import_dans_un_space_vierge(import_realise):
    """Import sans erreur NI référence manquante.

    Une référence manquante ne fait pas échouer l'import : elle produit un
    tableau de bord qui s'ouvre et dont les panneaux sont vides. C'est le défaut
    le plus courant d'un export mal fait — d'où le contrôle explicite ci-dessous.
    """
    assert import_realise.get("success") is True, (
        f"import en échec : {json.dumps(import_realise)[:600]}"
    )
    assert not import_realise.get("errors"), f"erreurs d'import : {import_realise.get('errors')}"
    assert import_realise.get("successCount") >= len(TABLEAUX), (
        f"{import_realise.get('successCount')} objet(s) importé(s), {len(TABLEAUX)} attendus"
    )
    for identifiant in TABLEAUX:
        assert identifiant in import_realise["_correspondance"], (
            f"{identifiant} absent du résultat d'import"
        )


def test_aucune_reference_manquante(kbn, space_vierge, import_realise):
    for origine, cible_id in import_realise["_correspondance"].items():
        r = kbn.get(
            f"{kbn.base}/s/{space_vierge}/api/saved_objects/dashboard/{cible_id}", timeout=60
        )
        assert r.status_code == 200, (
            f"{origine} (importé sous {cible_id}) introuvable — HTTP {r.status_code}"
        )
        for reference in r.json().get("references", []):
            cible = kbn.get(
                f"{kbn.base}/s/{space_vierge}/api/saved_objects/"
                f"{reference['type']}/{reference['id']}",
                timeout=60,
            )
            assert cible.status_code == 200, (
                f"{origine} référence {reference['type']}:{reference['id']}, introuvable"
            )


def test_les_panneaux_importes_ne_sont_pas_vides(kbn, space_vierge, import_realise):
    """Un tableau de bord importé sans ses panneaux s'ouvre quand même, vide.

    Le contrôle porte donc sur le contenu réel de l'objet importé, et pas
    seulement sur son existence.
    """
    for origine, cible_id in import_realise["_correspondance"].items():
        objet = kbn.get(
            f"{kbn.base}/s/{space_vierge}/api/saved_objects/dashboard/{cible_id}", timeout=60
        ).json()
        panneaux = objet["attributes"].get("panels") or objet["attributes"].get("panelsJSON")
        assert panneaux, f"{origine} importé sans panneau"
        nombre = len(panneaux) if isinstance(panneaux, list) else len(json.loads(panneaux))
        assert nombre >= 5, f"{origine} : {nombre} panneau(x) après import"


def test_chaque_panneau_se_rend_sans_erreur(lab_demarre):
    """Un panneau en erreur s'affiche quand même : seul le rendu le révèle."""
    defauts = {}
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        for identifiant in TABLEAUX:
            K.ouvrir_tableau_de_bord(page, identifiant, espace=ESPACE_CORRIGES)
            nombre = page.locator(K.ts("panneau")).count()
            erreurs = K.panneaux_en_erreur(page)
            if nombre == 0:
                defauts[identifiant] = "aucun panneau rendu"
            elif erreurs:
                defauts[identifiant] = f"panneaux en erreur : {erreurs}"
    assert not defauts, f"rendu défectueux : {defauts}"


def test_au_plus_douze_panneaux(config):
    """Règle de conception de SPEC §6.2 (M3), que les corrigés doivent respecter."""
    for identifiant in TABLEAUX:
        corps = json.loads(
            (config.RACINE / "corriges" / f"{identifiant}.json").read_text(encoding="utf-8")
        )
        assert len(corps["panels"]) <= 12, (
            f"{identifiant} : {len(corps['panels'])} panneaux, 12 au plus"
        )
        assert corps["description"], f"{identifiant} sans description (public + question)"


def test_les_decomptes_publies_correspondent_aux_corriges(config):
    """Un chiffre publié qu'aucun contrôle ne recompte est celui qui dérive.

    Le rapport de recette annonçait « Vue IDS (7 panneaux) » et « les 12
    panneaux se rendent sans erreur » alors que l'écran en porte huit depuis
    qu'un panneau de gravité dans le temps lui a été ajouté, et que le total
    vaut treize. Le même document imprimait pourtant, trois cents lignes plus
    bas, la sortie « [OK] Vue IDS 8 panneaux » : il se contredisait tout seul.

    C'est un manquement aux statuts honnêtes de CLAUDE.md, pas une coquille :
    le lecteur n'a aucun moyen de savoir lequel des deux chiffres croire. On
    recompte donc les panneaux dans les corrigés eux-mêmes et on exige que les
    documents le disent.
    """
    import re

    reels = {}
    for identifiant in TABLEAUX:
        chemin = config.RACINE / "corriges" / f"{identifiant}.json"
        if not chemin.exists():
            pytest.skip(f"NON EXÉCUTÉ : {chemin.name} absent.")
        corps = json.loads(chemin.read_text(encoding="utf-8"))
        reels[corps["title"]] = len(corps["panels"])
    total = sum(reels.values())

    defauts = []
    for nom in ("docs/RAPPORT_RECETTE.md", "docs/JOURNAL.md"):
        document = config.RACINE / nom
        if not document.exists():
            continue
        texte = document.read_text(encoding="utf-8")

        # « Vue IDS » (8 panneaux) — le titre, puis son décompte.
        for titre, attendu in reels.items():
            for annonce in re.findall(
                rf"«\s*{re.escape(titre)}\s*»\s*\((\d+)\s+panneaux\)", texte
            ):
                if int(annonce) != attendu:
                    defauts.append(
                        f"{nom} : « {titre} » annoncé à {annonce} panneaux, "
                        f"le corrigé en porte {attendu}"
                    )

        # « les 13 panneaux se rendent sans erreur » — le total.
        for annonce in re.findall(r"les\s+(\d+)\s+panneaux\s+se\s+rendent", texte):
            if int(annonce) != total:
                defauts.append(
                    f"{nom} : total annoncé à {annonce} panneaux, réel {total}"
                )
        for annonce in re.findall(r"rendu\s+des\s+(\d+)\s+panneaux", texte):
            if int(annonce) != total:
                defauts.append(
                    f"{nom} : total annoncé à {annonce} panneaux, réel {total}"
                )

    assert not defauts, "décomptes de panneaux faux :\n  " + "\n  ".join(defauts)


def test_titres_formules_en_questions(config):
    """SPEC §6.2 : les titres de panneaux sont formulés en questions."""
    manquants = []
    for identifiant in TABLEAUX:
        corps = json.loads(
            (config.RACINE / "corriges" / f"{identifiant}.json").read_text(encoding="utf-8")
        )
        for panneau in corps["panels"]:
            titre = panneau["config"].get("title", "")
            if not titre.strip().endswith("?"):
                manquants.append(f"{identifiant} : « {titre} »")
    assert not manquants, "titres non formulés en questions :\n  " + "\n  ".join(manquants)


def _nombre(texte: str) -> int | None:
    """Extrait le premier nombre d'un panneau d'indicateur.

    Kibana formate les milliers selon la locale : « 384 087 », « 384,087 »…
    """
    # Espace ordinaire, insécable (\u00a0), insécable étroite (\u202f), virgule
    # et point : tous employés comme séparateurs de milliers selon la locale.
    separateurs = " \u00a0\u202f,."
    classe = "".join("\\" + c if c in ".^]\\-" else c for c in separateurs)
    trouve = re.search(rf"(\d[\d{classe}]*\d|\d)", texte)
    if not trouve:
        return None
    brut = re.sub(rf"[{classe}]", "", trouve.group(1))
    return int(brut) if brut.isdigit() else None


def test_valeurs_affichees_egales_a_elasticsearch(es, config, lab_demarre):
    """« Valeurs affichées = manifeste » (SPEC §10).

    La comparaison se fait contre ce qu'Elasticsearch répond POUR LA MÊME
    FENÊTRE que le tableau de bord (« now-7d » à « now »), et non contre le
    total figé du manifeste : les données étant en fenêtre glissante, ce total
    vieillit dès que le temps passe. Comparer au manifeste brut ferait échouer
    un contrôle pourtant juste.
    """
    motif = str(config.valeur("donnees.data_view_motif"))
    attendu = es.post(
        f"{es.base}/{motif}/_count",
        json={"query": {"range": {"@timestamp": {"gte": "now-7d", "lte": "now"}}}},
        timeout=90,
    ).json()["count"]

    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        K.ouvrir_tableau_de_bord(page, "kit-soc-sante-collecte", espace=ESPACE_CORRIGES)
        textes = K.textes_des_panneaux(page)

    panneau = next((t for t in textes if "Combien d'événements" in t), None)
    assert panneau, f"panneau d'indicateur introuvable parmi {len(textes)} panneaux"
    affiche = _nombre(panneau.split("Événements collectés")[-1])
    assert affiche is not None, f"valeur illisible dans : {panneau[:200]!r}"

    # Tolérance d'une seconde de décalage entre les deux mesures : la fenêtre
    # glisse pendant l'exécution du contrôle.
    ecart = abs(affiche - attendu)
    assert ecart <= max(50, attendu * 0.001), (
        f"le tableau affiche {affiche}, Elasticsearch compte {attendu} "
        f"sur la même fenêtre (écart {ecart})"
    )


def test_le_tableau_de_sante_revele_la_source_muette(lab_demarre):
    """Le corrigé doit rendre S6 visible : c'est sa raison d'être.

    Une source muette ne produit aucun bucket ; elle disparaît d'un décompte par
    source. Le corrigé la fait ressortir de deux façons : l'indicateur « sources
    actives sur la dernière heure » passe sous six, et la source muette arrive en
    tête du tableau « dernier événement vu ».
    """
    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        K.ouvrir_tableau_de_bord(page, "kit-soc-sante-collecte", espace=ESPACE_CORRIGES)
        textes = K.textes_des_panneaux(page)

    actives = next((t for t in textes if "dernière heure" in t), None)
    assert actives, "panneau « sources actives » absent"
    valeur = _nombre(actives.split("Sources actives")[-1])
    assert valeur is not None and valeur < 6, (
        f"l'indicateur affiche {valeur} : il devrait passer sous six, "
        "une source étant muette depuis deux heures"
    )

    dernier = next((t for t in textes if "dernière fois" in t), None)
    assert dernier, "panneau « dernier événement vu par source » absent"
    lignes = [ligne for ligne in dernier.split("\n") if ligne.strip()]
    assert any("firewall.traffic" in ligne for ligne in lignes), (
        "la source muette n'apparaît pas dans le tableau du dernier événement vu"
    )
