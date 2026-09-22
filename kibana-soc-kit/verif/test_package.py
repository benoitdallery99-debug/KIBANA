"""verif-package — ce que prouve cette suite (SPEC §10) :

les empreintes de `SHA256SUMS` sont valides ; l'archive contient tout ce dont
le poste cible a besoin ; l'installation se déroule dans un répertoire vierge
SANS aucun accès réseau ; le guide livré s'ouvre hors ligne et sa validation de
réponse fonctionne.

Ce que cette suite ne prouve PAS, et où c'est prouvé : le fonctionnement du lab
sur un réseau podman « --internal » est établi par verif-lab, qui crée un pod
dédié sur un tel réseau. Le refaire ici demanderait un second lab complet en
mémoire, sans rien démontrer de plus.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from verif.e2e import kibana as K

pytestmark = pytest.mark.package


@pytest.fixture(scope="module")
def archive(config):
    trouvees = sorted((config.RACINE / "dist").glob("kit-formation-kibana-*.tar.gz"))
    if not trouvees:
        pytest.skip("NON EXÉCUTÉ : aucune archive dans dist/. Lancez « make package ».")
    return trouvees[-1]


@pytest.fixture(scope="module")
def extraite(archive):
    """Extrait l'archive dans un répertoire vierge, comme sur le poste cible."""
    with tempfile.TemporaryDirectory(prefix="kit-verif-package-") as dossier:
        with tarfile.open(archive, "r:gz") as t:
            t.extractall(dossier, filter="data")
        racines = [p for p in Path(dossier).iterdir() if p.is_dir()]
        assert len(racines) == 1, f"l'archive devrait contenir un seul dossier : {racines}"
        yield racines[0]


def test_empreinte_de_l_archive(archive):
    empreinte = archive.with_suffix(archive.suffix + ".sha256")
    if not empreinte.exists():
        pytest.skip("NON EXÉCUTÉ : empreinte de l'archive absente.")
    attendu = empreinte.read_text(encoding="utf-8").split()[0]
    calcule = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert calcule == attendu, "l'archive ne correspond pas à son empreinte"


def test_sha256sums_valide(extraite):
    """Toutes les lignes de SHA256SUMS doivent passer, sans exception."""
    fichier = extraite / "SHA256SUMS"
    assert fichier.exists(), "SHA256SUMS absent de l'archive"

    resultat = subprocess.run(
        ["sha256sum", "-c", "--quiet", "SHA256SUMS"],
        cwd=extraite, capture_output=True, text=True, check=False, timeout=600,
    )
    assert resultat.returncode == 0, (
        "empreintes non conformes :\n" + resultat.stdout[-2000:] + resultat.stderr[-500:]
    )
    assert len(fichier.read_text(encoding="utf-8").splitlines()) > 40


def test_archive_complete(extraite):
    """Tout ce dont le poste cible a besoin doit voyager avec l'archive."""
    attendus = [
        "guide.html", "README.md", "INSTALLATION.md", "installer.sh",
        "kit.config.yaml", "Makefile", "exigences.txt",
        "lab/pod.yaml.tmpl", "lab/preflight.sh", "lab/lab-up.sh", "lab/init/init.py",
        "data/generateur/engendrer.py", "data/manifest.json",
        "corriges/tableaux-de-bord.ndjson",
        "guide/polices/OFL-AtkinsonHyperlegibleNext.txt",
        "docs/capacites.md",
    ]
    manquants = [c for c in attendus if not (extraite / c).exists()]
    assert not manquants, f"absents de l'archive : {manquants}"

    images = list((extraite / "images").glob("*.tar"))
    assert len(images) >= 2, f"{len(images)} image(s) de conteneur, 2 attendues"
    for image in images:
        assert image.stat().st_size > 100 * 1024 * 1024, f"{image.name} suspicieusement petite"


def test_le_manifeste_de_l_epreuve_n_est_pas_livre(extraite):
    """L'épreuve n'embarque aucune réponse, même sous forme d'empreinte (SPEC §9).

    Son manifeste reste côté formateur : livré avec le kit du stagiaire, il
    donnerait les réponses de l'évaluation.
    """
    assert not (extraite / "data" / "manifest-epreuve.json").exists(), (
        "le manifeste de l'épreuve est dans l'archive du stagiaire"
    )


def test_aucun_secret_dans_l_archive(extraite):
    """Les mots de passe sont engendrés à l'installation, jamais livrés."""
    assert not (extraite / ".env").exists(), ".env est dans l'archive"
    suspects = []
    for chemin in extraite.rglob("*"):
        if chemin.is_file() and chemin.name in (".env", "pod.yaml"):
            suspects.append(str(chemin.relative_to(extraite)))
    assert not suspects, f"fichiers porteurs de secrets livrés : {suspects}"


def test_installation_sans_acces_reseau(extraite):
    """L'installation ne doit joindre aucun réseau.

    Le contrôle porte sur pip, seul composant susceptible de sortir : il est
    lancé avec « --no-index » et un dossier de wheels local, et toute variable
    de proxy est pointée vers un port mort. S'il tentait d'atteindre PyPI, il
    échouerait au lieu de réussir silencieusement.
    """
    wheels = extraite / "wheels"
    if not wheels.exists() or not any(wheels.iterdir()):
        pytest.skip("NON EXÉCUTÉ : wheels/ vide dans l'archive.")

    environnement = dict(os.environ)
    for variable in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        environnement[variable] = "http://127.0.0.1:1"
    environnement["PIP_NO_INDEX"] = "1"

    venv = extraite / ".venv-essai"
    subprocess.run(
        ["python3", "-m", "venv", str(venv)],
        check=True, capture_output=True, timeout=300,
    )
    resultat = subprocess.run(
        [str(venv / "bin" / "pip"), "install", "--no-index",
         "--find-links", str(wheels), "-r", str(extraite / "exigences.txt")],
        capture_output=True, text=True, env=environnement, check=False, timeout=900,
    )
    assert resultat.returncode == 0, (
        "installation hors ligne en échec :\n"
        + resultat.stdout[-1500:] + resultat.stderr[-1500:]
    )
    sortie = resultat.stdout + resultat.stderr
    for marque in ("pypi.org", "files.pythonhosted.org", "Downloading http"):
        assert marque not in sortie, f"pip a joint le réseau : « {marque} » dans sa sortie"


def test_preflight_de_l_archive_s_execute(extraite):
    """Le pré-vol livré doit s'exécuter et rendre un diagnostic lisible."""
    resultat = subprocess.run(
        ["bash", "lab/preflight.sh"],
        cwd=extraite, capture_output=True, text=True, check=False, timeout=300,
    )
    sortie = resultat.stdout + resultat.stderr
    assert "Résultat" in sortie, f"pré-vol sans conclusion :\n{sortie[-800:]}"
    for rubrique in ("Runtime de conteneurs", "Mémoire", "Espace disque", "Images"):
        assert rubrique in sortie, f"le pré-vol ne contrôle pas « {rubrique} »"


def test_le_guide_livre_s_ouvre_hors_ligne(extraite):
    """Le guide de l'archive doit s'ouvrir seul et valider une réponse."""
    guide = extraite / "guide.html"
    with sync_playwright() as p:
        lanceur = p.chromium.launch(
            executable_path=K.CHROMIUM if Path(K.CHROMIUM).exists() else None,
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        contexte = lanceur.new_context(locale="fr-FR", timezone_id="Europe/Paris")
        page = contexte.new_page()
        externes: list[str] = []
        page.on("request", lambda r: (
            externes.append(r.url)
            if not r.url.startswith(("file://", "data:", "blob:")) else None
        ))
        page.goto(f"file://{guide.resolve()}", wait_until="networkidle")
        page.wait_for_timeout(1200)

        assert not externes, f"le guide livré a tenté {len(externes)} requête(s)"
        titre = page.title()
        assert "Kibana" in titre, f"titre inattendu : {titre!r}"
        modules = page.locator("[data-ancre]").count()
        assert modules >= 2, f"{modules} section(s) dans le guide livré"
        contexte.close()
        lanceur.close()


# --------------------------------------------------------------------------
# Les chiffres que le rapport de recette publie
# --------------------------------------------------------------------------

def test_le_rapport_publie_le_vrai_nombre_de_controles(config):
    """Un tableau de bilan que rien ne recompte vieillit à chaque contrôle ajouté.

    Le rapport annonçait « verif-lab 17 », « verif-parcours 24 », « verif-guide
    18 » et un total de 99 alors que les suites en comptaient respectivement 18,
    31, 25 et 115. Un lecteur qui veut savoir ce que le kit prouve lit ce
    tableau, pas le code ; un chiffre faux y vaut une preuve fausse.

    On recompte les fonctions de test de chaque suite, on les rattache à leur
    marque par « pytestmark », et on exige que le tableau le dise — total
    compris.
    """
    rapport = config.RACINE / "docs" / "RAPPORT_RECETTE.md"
    if not rapport.exists():
        pytest.skip("NON EXÉCUTÉ : docs/RAPPORT_RECETTE.md absent.")
    texte = rapport.read_text(encoding="utf-8")

    reels: dict[str, int] = {}
    for chemin in sorted((config.RACINE / "verif").glob("test_*.py")):
        source = chemin.read_text(encoding="utf-8")
        marque = re.search(r"^pytestmark = pytest\.mark\.(\w+)", source, re.M)
        if not marque:
            continue
        reels[marque.group(1)] = len(re.findall(r"^def test_", source, re.M))
    assert reels, "aucune suite reconnue dans verif/"

    defauts = []
    vus = set()
    for marque, annonce, repete in re.findall(
        r"\|\s*`verif-(\w+)`\s*\|\s*(\d+)\s*\|\s*✅\s*(\d+)\s+pass", texte
    ):
        vus.add(marque)
        reel = reels.get(marque)
        if reel is None:
            defauts.append(f"verif-{marque} : suite inconnue de verif/")
            continue
        if int(annonce) != reel:
            defauts.append(
                f"verif-{marque} : {annonce} contrôles annoncés, {reel} écrits"
            )
        if annonce != repete:
            defauts.append(
                f"verif-{marque} : le tableau dit {annonce} puis {repete} passés"
            )

    manquantes = sorted(set(reels) - vus)
    if manquantes:
        defauts.append(
            "suites absentes du tableau : " + ", ".join(f"verif-{m}" for m in manquantes)
        )

    total = sum(reels.values())
    for annonce in re.findall(r"\|\s*\*\*Total\*\*\s*\|\s*\*\*(\d+)\*\*", texte):
        if int(annonce) != total:
            defauts.append(f"total annoncé {annonce}, réel {total}")

    assert not defauts, "chiffres du rapport de recette :\n  " + "\n  ".join(defauts)
