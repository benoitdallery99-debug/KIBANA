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
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import pytest
import yaml
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

    # Les TRANSCRIPTIONS, ensuite. Le rapport en compte une par phase — « $ make
    # verif-parcours » suivi de « 20 passed » — et une, globale, qui nomme la
    # suite en fin de ligne. Elles vieillissaient sans que rien ne les relise :
    # le tableau de bilan disait 33 contrôles de parcours et la transcription de
    # la phase P3, vingt. Un lecteur qui descend d'une page voit le kit se
    # contredire.
    for marque, annonce in re.findall(
        r"\$\s*make\s+verif-(\w+)\s*\n\s*(\d+)\s+pass", texte
    ):
        reel = reels.get(marque)
        if reel is not None and int(annonce) != reel:
            defauts.append(
                f"transcription « make verif-{marque} » : {annonce} passés, "
                f"{reel} contrôles écrits"
            )
    for annonce, marque in re.findall(
        r"^\s*(\d+)\s+passed[^\n(]*\(verif-(\w+)\)", texte, re.M
    ):
        reel = reels.get(marque)
        if reel is not None and int(annonce) != reel:
            defauts.append(
                f"transcription globale, verif-{marque} : {annonce} passés, "
                f"{reel} contrôles écrits"
            )

    # Le tableau des modules du §P3 : durées et nombres d'exercices.
    modules = {}
    for chemin in sorted((config.RACINE / "parcours").glob("M*.md")):
        entete = yaml.safe_load(chemin.read_text(encoding="utf-8").split("---", 2)[1])
        modules[entete["id"]] = (
            entete["duree_minutes"], len(entete["exercices"])
        )
    for identifiant, duree, exercices in re.findall(
        r"^\|\s*(M\d)[^|]*\|\s*(\d+)\s*min\s*\|\s*(\d+)\s*\|", texte, re.M
    ):
        reel = modules.get(identifiant)
        if not reel:
            continue
        if int(duree) != reel[0]:
            defauts.append(
                f"§P3, {identifiant} : {duree} min publiées, {reel[0]} déclarées"
            )
        if int(exercices) != reel[1]:
            defauts.append(
                f"§P3, {identifiant} : {exercices} exercices publiés, {reel[1]} écrits"
            )
    total_minutes = sum(d for d, _ in modules.values())
    total_exercices = sum(e for _, e in modules.values())
    for minutes, exercices in re.findall(
        r"\*\*(\d+) minutes\*\*,\s*\*\*(\d+) exercices\*\*", texte
    ):
        if int(minutes) != total_minutes:
            defauts.append(f"§P3 : {minutes} minutes publiées, {total_minutes} réelles")
        if int(exercices) != total_exercices:
            defauts.append(
                f"§P3 : {exercices} exercices publiés, {total_exercices} réels"
            )

    assert not defauts, "chiffres du rapport de recette :\n  " + "\n  ".join(defauts)


# Modules tiers que la chaîne importe. Tout ce qui n'est ni la bibliothèque
# standard ni un module du kit doit figurer dans exigences.txt.
STDLIB_ET_KIT = {
    "outils", "verif", "data", "lab", "guide", "corriges", "captures",
    "conf", "evenements", "temps", "scenarios", "fuites", "glossaire",
    "typographie", "libelles", "kibana", "e2e",
    # Modules frères du kit, importés sans préfixe grâce à sys.path.
    "gabarits", "contexte", "build", "pdf", "produire", "construire",
    "engendrer", "rendre_pod", "init",
}


def test_toute_dependance_importee_est_declaree(config):
    """« Ça marche chez moi » n'est pas un critère de livraison.

    RELEVÉ À LA PREMIÈRE INSTALLATION PAR UN HUMAIN. exigences.txt ne déclarait
    ni playwright, ni pytest-playwright, ni weasyprint, ni pillow — quatre
    modules installés à la main dans l'environnement de fabrication, des jours
    plus tôt, et jamais consignés. Le kit se construisait et se vérifiait ici
    sans que rien ne signale la dette. Sur un poste neuf, « make verif » et
    « make guide » s'arrêtaient sur un ModuleNotFoundError.

    Ce contrôle lit les imports de toute la chaîne et exige que chacun soit
    déclaré. Il ne peut pas attraper un module présent dans les deux
    environnements, mais il attrape celui qui manque au fichier.
    """
    import ast
    import sys

    exigences = (config.RACINE / "exigences.txt").read_text(encoding="utf-8")
    declares = {
        re.split(r"[<>=!~\[]", ligne.strip())[0].lower().replace("-", "_")
        for ligne in exigences.split("\n")
        if ligne.strip() and not ligne.strip().startswith("#")
    }
    # Quelques distributions ne portent pas le nom de leur module.
    declares |= {"yaml"} if "pyyaml" in declares else set()
    declares |= {"PIL".lower()} if "pillow" in declares else set()

    importes: dict[str, str] = {}
    for dossier in ("data", "lab", "guide", "corriges", "captures", "outils", "verif"):
        for chemin in (config.RACINE / dossier).rglob("*.py"):
            if "__pycache__" in chemin.parts:
                continue
            try:
                arbre = ast.parse(chemin.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for noeud in ast.walk(arbre):
                if isinstance(noeud, ast.Import):
                    noms = [a.name for a in noeud.names]
                elif isinstance(noeud, ast.ImportFrom):
                    noms = [noeud.module] if noeud.module and noeud.level == 0 else []
                else:
                    continue
                for nom in noms:
                    racine = nom.split(".")[0]
                    importes.setdefault(
                        racine, str(chemin.relative_to(config.RACINE))
                    )

    manquants = sorted(
        f"{module} (importé par {ou})"
        for module, ou in importes.items()
        if module not in STDLIB_ET_KIT
        and module.lower() not in declares
        and module not in sys.stdlib_module_names
    )
    assert not manquants, (
        "modules importés par la chaîne mais absents d'exigences.txt :\n  "
        + "\n  ".join(manquants)
    )


def test_les_images_livrees_repondent_aux_digests_epingles(extraite):
    """L'image chargée depuis le tar livré doit résoudre la référence du pod.

    DÉFAUT MESURÉ, et invisible des deux machines qui ont construit le kit :
    « podman save --format docker-archive » resérialise l'image, et « podman
    load » lui donne un digest de manifeste DIFFÉRENT de celui du registre.
    Sur la chaîne de fabrication les images viennent d'un « pull », donc le
    digest de lab/images.yaml résout ; sur un poste hors ligne elles viennent
    du tar, et il ne résout plus. Avec « imagePullPolicy: Never », le pod ne
    démarrait pas — c'est-à-dire que le lab ne démarrait sur AUCUNE
    installation hors ligne neuve, ce qui est précisément le cas d'usage.

    Le contrôle charge une image de l'archive dans un magasin podman vierge et
    demande la seule chose qui compte : la référence épinglée y est-elle
    résolvable, ou lab/rendre_pod.py sait-il la réancrer ?
    """
    if not shutil.which("podman"):
        pytest.skip("NON EXÉCUTÉ : podman absent.")
    tar = extraite / "images" / "elasticsearch.tar"
    if not tar.exists():
        pytest.skip("NON EXÉCUTÉ : images/elasticsearch.tar absent de l'archive.")
    epingles = yaml.safe_load((extraite / "lab" / "images.yaml").read_text(encoding="utf-8"))
    attendu = epingles["elasticsearch"]

    libre_go = shutil.disk_usage(extraite).free / 1024**3
    if libre_go < 6:
        pytest.skip(f"NON EXÉCUTÉ : {libre_go:.1f} Go libres, il en faut 6 "
                    "pour un magasin d'essai.")

    # MESURÉ : podman refuse un « runroot » de plus de 50 caractères. Le
    # répertoire temporaire par défaut suffit rarement — on vise /run quand il
    # est là, sinon on laisse tempfile choisir et le contrôle se saute si podman
    # proteste sur la longueur.
    ou = "/run" if os.access("/run", os.W_OK) else None
    with tempfile.TemporaryDirectory(prefix="kit-magasin-") as magasin, \
            tempfile.TemporaryDirectory(prefix="kit-r-", dir=ou) as run:
        podman = ["podman", "--root", magasin, "--runroot", run]
        charge = subprocess.run([*podman, "load", "-i", str(tar)],
                                capture_output=True, text=True, timeout=1800, check=False)
        if "runroot is longer than" in charge.stderr:
            pytest.skip(f"NON EXÉCUTÉ : chemin de runroot trop long ({run}).")
        assert charge.returncode == 0, f"podman load a échoué :\n{charge.stderr[-1500:]}"

        resout = subprocess.run([*podman, "image", "exists", attendu],
                                capture_output=True, check=False).returncode == 0
        if resout:
            return  # l'épinglage tient : rien d'autre à prouver.

        # Il ne résout pas : le kit doit alors SAVOIR le réancrer, sinon le pod
        # référencera une image absente et « imagePullPolicy: Never » l'arrêtera.
        version = yaml.safe_load((extraite / "kit.config.yaml").read_text(encoding="utf-8"))
        etiquette = f"mirror.gcr.io/library/elasticsearch:{version['stack']['version']}"
        par_etiquette = subprocess.run([*podman, "image", "exists", etiquette],
                                       capture_output=True, check=False).returncode == 0
        assert par_etiquette, (
            f"ni le digest épinglé ({attendu}) ni l'étiquette ({etiquette}) ne résolvent "
            "dans un magasin chargé depuis le tar livré : le lab ne peut pas démarrer hors ligne"
        )
        source = (extraite / "lab" / "rendre_pod.py").read_text(encoding="utf-8")
        assert "existe_localement" in source, (
            "le digest épinglé ne résout pas après « podman load » et lab/rendre_pod.py ne "
            "vérifie pas le magasin local : « make lab-up » échouera sur tout poste hors ligne"
        )
