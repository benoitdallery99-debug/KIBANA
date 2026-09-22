"""verif-lab — ce que prouve cette suite (SPEC §10) :

licence « basic », santé « green », Kibana disponible et à la bonne version,
locale et vue de solution conformes à kit.config.yaml, initialisation en place,
et fonctionnement sur un réseau podman « --internal » sans accès extérieur (§4.6).
"""

from __future__ import annotations

import subprocess
import time

import pytest
import yaml

pytestmark = pytest.mark.lab


# --------------------------------------------------------------------------
# Elasticsearch
# --------------------------------------------------------------------------

def test_licence_est_basic(es, lab_demarre):
    """Le parcours n'enseigne que ce qui existe en Basic : la licence doit l'être.

    Le script start-local d'Elastic active un trial de 30 jours ; le lab ne
    l'utilise pas (CLAUDE.md).
    """
    licence = es.get(f"{es.base}/_license", timeout=15).json()["license"]
    assert licence["type"] == "basic", f"licence « {licence['type']} », attendu « basic »"
    assert licence["status"] == "active", f"licence non active : {licence['status']}"


def test_sante_cluster_green(es, lab_demarre):
    """Nœud unique, réplicas à 0 : la santé attendue est « green », pas « yellow »."""
    sante = es.get(f"{es.base}/_cluster/health", timeout=15).json()
    assert sante["status"] == "green", (
        f"santé « {sante['status']} », {sante['unassigned_shards']} shard(s) non assigné(s). "
        "Vérifiez les seuils d'occupation disque (lab/pod.yaml.tmpl)."
    )


def test_version_elasticsearch_conforme(es, config, lab_demarre):
    racine = es.get(f"{es.base}/", timeout=15).json()
    assert racine["version"]["number"] == config.version(), (
        f"Elasticsearch {racine['version']['number']}, "
        f"or kit.config.yaml annonce {config.version()}"
    )


# --------------------------------------------------------------------------
# Kibana
# --------------------------------------------------------------------------

def test_kibana_disponible_et_conforme(kbn, config, lab_demarre):
    etat = kbn.get(f"{kbn.base}/api/status", timeout=30).json()
    niveau = etat["status"]["overall"]["level"]
    assert niveau == "available", f"Kibana au niveau « {niveau} »"
    assert etat["version"]["number"] == config.version(), (
        f"Kibana {etat['version']['number']}, or kit.config.yaml annonce {config.version()}"
    )


def test_locale_kibana_conforme(kbn, config, lab_demarre):
    """La langue de l'interface décide des libellés cités dans le guide.

    Kibana sert ses traductions sur /translations/<locale>.json : si le fichier
    existe et n'est pas vide, la locale est bien chargée.
    """
    locale = str(config.valeur("kibana.locale"))
    r = kbn.get(f"{kbn.base}/translations/{locale}.json", timeout=30)
    assert r.status_code == 200, f"locale {locale} non servie par Kibana (HTTP {r.status_code})"
    messages = r.json().get("messages", {})
    assert len(messages) > 1000, f"locale {locale} servie mais quasi vide ({len(messages)} clés)"


def test_vue_de_solution_du_space(kbn, config, lab_demarre):
    """La vue de solution change toute la navigation depuis la 8.16 (SPEC §4.3)."""
    space_id = str(config.valeur("formation.space_id"))
    attendue = str(config.valeur("kibana.vue_solution"))
    r = kbn.get(f"{kbn.base}/api/spaces/space/{space_id}", timeout=30)
    assert r.status_code == 200, f"Space « {space_id} » absent (HTTP {r.status_code})"
    obtenue = r.json().get("solution")
    assert obtenue == attendue, f"vue de solution « {obtenue} », attendu « {attendue} »"


def test_data_views_a_id_fixe(kbn, config, lab_demarre):
    """Les ID fixes rendent les tableaux de bord réutilisables sur la cible (M5).

    Chacune vit dans le Space qui la concerne : celle du parcours dans le Space
    de formation, celle de l'épreuve dans le Space de l'épreuve.
    """
    space_formation = str(config.valeur("formation.space_id"))
    for prefixe, space_id in (("donnees", space_formation), ("epreuve", "epreuve")):
        dv_id = str(config.valeur(f"{prefixe}.data_view_id"))
        motif = str(config.valeur(f"{prefixe}.data_view_motif"))
        r = kbn.get(f"{kbn.base}/s/{space_id}/api/data_views/data_view/{dv_id}", timeout=30)
        assert r.status_code == 200, (
            f"data view « {dv_id} » absente du Space « {space_id} » "
            f"(HTTP {r.status_code})"
        )
        dv = r.json()["data_view"]
        assert dv["title"] == motif, f"data view « {dv_id} » pointe {dv['title']}, attendu {motif}"
        assert dv["timeFieldName"] == "@timestamp"


def test_le_jeu_de_l_epreuve_est_hors_du_space_de_formation(kbn, config, lab_demarre):
    """La data view de l'épreuve ne doit PAS être visible depuis la formation.

    Laissée là, elle annonce au stagiaire, dès le sélecteur de source de
    Discover, qu'un second jeu de données existe — et son motif d'index le
    renseigne sur ce qui l'attend à l'évaluation.
    """
    space_formation = str(config.valeur("formation.space_id"))
    dv_id = str(config.valeur("epreuve.data_view_id"))
    r = kbn.get(
        f"{kbn.base}/s/{space_formation}/api/data_views/data_view/{dv_id}", timeout=30
    )
    assert r.status_code == 404, (
        f"la data view « {dv_id} » est visible depuis le Space de formation "
        f"(HTTP {r.status_code}) : le jeu de l'épreuve y est annoncé"
    )


def test_le_fuseau_d_affichage_est_celui_du_metier(kbn, config, lab_demarre):
    """Deux réponses notées sont des HEURES : l'écran doit les afficher dans le
    fuseau où le manifeste les calcule.

    Kibana laisse « dateFormat:tz » sur « Browser ». Sur un poste en UTC, M2-E6
    et M4-E7 affichent deux heures de moins que ce que l'empreinte attend, et la
    réponse juste est refusée sans un mot. Le contrôle de bout en bout ne
    pouvait pas le voir : il pilote un navigateur dont le fuseau est forcé sur
    celui du métier. Celui-ci lit le réglage du serveur, qui est ce que verra
    le stagiaire.
    """
    fuseau = str(config.valeur("donnees.fuseau_metier"))
    espaces = [
        str(config.valeur("formation.space_id")),
        "reseau", "corriges", "epreuve",
    ]
    defauts = []
    for space_id in espaces:
        # « /api/kibana/settings » est documentée publique, mais 9.5.3 répond
        # 400 « exists but is not available with the current configuration »
        # tant que l'appel ne se déclare pas d'origine interne — relevé en lab
        # sur les deux routes, « /api/ » et « /internal/ ».
        r = kbn.get(
            f"{kbn.base}/s/{space_id}/api/kibana/settings",
            headers={"x-elastic-internal-origin": "Kibana"},
            timeout=60,
        )
        if r.status_code != 200:
            defauts.append(f"{space_id} : réglages illisibles (HTTP {r.status_code})")
            continue
        pose = (r.json().get("settings", {}).get("dateFormat:tz") or {}).get("userValue")
        if pose != fuseau:
            defauts.append(
                f"{space_id} : dateFormat:tz = {pose!r}, attendu {fuseau!r} — "
                "l'heure affichée serait celle du poste du stagiaire"
            )
    assert not defauts, "fuseau d'affichage :\n  " + "\n  ".join(defauts)


def test_roles_et_comptes(kbn, es, lab_demarre):
    for role in ("formateur", "stagiaire"):
        r = kbn.get(f"{kbn.base}/api/security/role/{role}", timeout=30)
        assert r.status_code == 200, f"rôle « {role} » absent (HTTP {r.status_code})"
    for compte in ("formateur", "stagiaire"):
        r = es.get(f"{es.base}/_security/user/{compte}", timeout=15)
        assert r.status_code == 200, f"compte « {compte} » absent (HTTP {r.status_code})"


def test_kibana_se_connecte_avec_kibana_system(config, lab_demarre):
    """Depuis la 8.0, le superutilisateur « elastic » est interdit à Kibana."""
    rendu = (config.RACINE / "lab" / "generated" / "pod.yaml").read_text(encoding="utf-8")
    assert "ELASTICSEARCH_USERNAME" in rendu
    assert "kibana_system" in rendu, "Kibana doit se connecter avec kibana_system"


# --------------------------------------------------------------------------
# Hors ligne et isolation réseau (SPEC §4.6)
# --------------------------------------------------------------------------

def test_aucun_telechargement_a_l_execution(config):
    """imagePullPolicy: Never — le lab ne tente jamais de tirer une image.

    Le contrôle porte sur le YAML analysé, conteneur par conteneur : compter les
    occurrences dans le texte compterait aussi les commentaires.
    """
    chemin = config.RACINE / "lab" / "generated" / "pod.yaml"
    docs = [d for d in yaml.safe_load_all(chemin.read_text(encoding="utf-8")) if d]
    pods = [d for d in docs if d.get("kind") == "Pod"]
    assert len(pods) == 1, f"un seul Pod attendu, {len(pods)} trouvé(s)"

    conteneurs = pods[0]["spec"]["containers"]
    assert len(conteneurs) == 2, f"deux conteneurs attendus, {len(conteneurs)} trouvé(s)"
    for c in conteneurs:
        assert c.get("imagePullPolicy") == "Never", (
            f"conteneur « {c['name']} » : imagePullPolicy = {c.get('imagePullPolicy')!r}, "
            "attendu « Never » (le lab ne télécharge rien)"
        )
        assert "@sha256:" in c["image"], (
            f"conteneur « {c['name']} » : image non épinglée par digest ({c['image']})"
        )


def test_cartes_et_telemetrie_coupees(config):
    """Sans ces réglages, Kibana attend un service en ligne et le lab se fige."""
    rendu = (config.RACINE / "lab" / "generated" / "pod.yaml").read_text(encoding="utf-8")
    for reglage in (
        "MAP_INCLUDEELASTICMAPSSERVICE",
        "TELEMETRY_ENABLED",
        "NEWSFEED_ENABLED",
    ):
        assert reglage in rendu, f"réglage {reglage} absent du pod"


def _podman(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["podman", *args], capture_output=True, text=True, timeout=timeout, check=False
    )


@pytest.fixture(scope="module")
def reseau_interne(config):
    """Crée un réseau podman « --internal » (sans route vers l'extérieur).

    Le démontage DÉTACHE le pod du réseau avant de supprimer celui-ci. Un
    « network rm -f » supprimerait aussi les conteneurs qui y sont rattachés,
    c'est-à-dire le lab lui-même : une vérification ne doit jamais détruire ce
    qu'elle vérifie (constaté en lab le 21/09/2026).
    """
    nom = "kibana-soc-verif-interne"
    if _podman("network", "exists", nom).returncode != 0:
        r = _podman("network", "create", "--internal", nom)
        if r.returncode != 0:
            pytest.skip(
                "NON EXÉCUTÉ : réseau interne impossible à créer "
                f"({r.stderr.strip()[:200]})"
            )
    yield nom

    infra = _infra_du_pod(config.NOM_POD)
    if infra:
        _podman("network", "disconnect", nom, infra)
    _podman("network", "rm", nom)


def _infra_du_pod(nom_pod: str) -> str:
    """Identifiant du conteneur d'infrastructure du pod.

    podman le nomme d'après l'ID du pod (« <id>-infra »), pas d'après son nom :
    il faut donc le demander au pod plutôt que de deviner le nom.
    """
    r = _podman("pod", "inspect", nom_pod, "--format", "{{.InfraContainerID}}")
    return r.stdout.strip() if r.returncode == 0 else ""


def _image_sonde(config) -> str:
    """Image utilisée pour les sondes : celle d'Elasticsearch, déjà locale et pourvue de curl."""
    chemin = config.RACINE / "lab" / "images.yaml"
    return yaml.safe_load(chemin.read_text(encoding="utf-8"))["elasticsearch"]


def _sonde(
    reseau: str, image: str, commande: str, timeout: int = 90
) -> subprocess.CompletedProcess:
    """Lance un conteneur jetable sur le réseau donné et y exécute une commande."""
    return _podman(
        "run", "--rm", "--network", reseau, "--entrypoint", "sh", image, "-c", commande,
        timeout=timeout,
    )


def _attendre(fn, limite: int, pas: int = 5):
    """Répète fn() jusqu'à ce qu'elle renvoie une valeur vraie, ou expire."""
    fin = time.time() + limite
    while time.time() < fin:
        valeur = fn()
        if valeur:
            return valeur
        time.sleep(pas)
    return None


def test_lab_fonctionne_sur_reseau_interne(config, reseau_interne, tmp_path_factory):
    """Le lab doit fonctionner sur un réseau podman « --internal » (SPEC §4.6).

    Le pod est CRÉÉ sur le réseau interne — le rattacher après coup ne suffit pas,
    le trafic entrant n'est alors pas routé (constaté en lab le 21/09/2026).
    Ce réseau ne publiant pas de ports vers l'hôte, les contrôles s'exécutent
    depuis un conteneur attaché au même réseau, comme le prévoit la SPEC.
    """
    nom = f"{config.NOM_POD}-interne"
    rendu = config.RACINE / "lab" / "generated" / "pod-interne.yaml"
    image = _image_sonde(config)
    secrets = config.secrets()

    rendre = subprocess.run(
        [
            str(config.RACINE / ".venv" / "bin" / "python"),
            str(config.RACINE / "lab" / "rendre_pod.py"),
            "--nom", nom,
            "--sortie", str(rendu),
            "--sans-hostports",
        ],
        capture_output=True, text=True, timeout=120, check=False,
    )
    assert rendre.returncode == 0, f"rendu du pod interne impossible : {rendre.stderr[:300]}"

    _podman("kube", "down", str(rendu), timeout=180)
    _podman("pod", "rm", "-f", nom, timeout=120)
    try:
        joue = _podman("kube", "play", "--network", reseau_interne, str(rendu), timeout=300)
        assert joue.returncode == 0, f"« kube play » a échoué : {joue.stderr[:400]}"

        def sonde(commande: str, timeout: int = 60) -> str:
            return _sonde(reseau_interne, image, commande, timeout=timeout).stdout

        # 1. Elasticsearch répond, depuis le réseau interne, sans aucun accès extérieur.
        #
        # PIÈGE : l'attente cherchait « "status" » dans la réponse. Or le corps
        # d'ERREUR en contient un lui aussi — « "status":503 » — et le nœud en
        # renvoie un tant que l'index .security-7 n'est pas alloué :
        # « failed to retrieve password hash for reserved user [elastic] ».
        # L'attente sortait donc au premier essai, sur l'erreur, et l'assertion
        # suivante échouait. On attend la santé du cluster, pas la présence d'un
        # mot-clé.
        def _sante_du_cluster() -> str | None:
            reponse = sonde(
                f"curl -sS -m 10 -u elastic:{secrets['ELASTIC_PASSWORD']} "
                f"http://{nom}:9200/_cluster/health"
            )
            if '"status":"green"' in reponse or '"status":"yellow"' in reponse:
                return reponse
            return None

        sante = _attendre(_sante_du_cluster, limite=300)
        assert sante, (
            "Elasticsearch n'a pas atteint green ou yellow sur le réseau interne "
            "après 300 s"
        )

        # 2. Kibana démarre et devient disponible, toujours sans accès extérieur.
        pose = _attendre(
            lambda: "200" == sonde(
                f"curl -sS -m 10 -o /dev/null -w '%{{http_code}}' -X POST "
                f"-u elastic:{secrets['ELASTIC_PASSWORD']} -H 'Content-Type: application/json' "
                f"-d '{{\"password\":\"{secrets['KIBANA_SYSTEM_PASSWORD']}\"}}' "
                f"http://{nom}:9200/_security/user/kibana_system/_password"
            ).strip(),
            limite=180,
        )
        assert pose, "mot de passe kibana_system impossible à fixer sur le réseau interne"

        etat = _attendre(
            lambda: (lambda s: s if '"level":"available"' in s else None)(
                sonde(f"curl -sS -m 15 http://{nom}:5601/api/status")
            ),
            limite=420,
        )
        assert etat, "Kibana n'est pas devenu disponible sur le réseau interne après 420 s"
    finally:
        _podman("kube", "down", str(rendu), timeout=180)
        _podman("pod", "rm", "-f", nom, timeout=120)
        _podman("volume", "rm", "-f", f"{nom}-es-data", timeout=120)


def test_reseau_interne_interdit_toute_sortie(config, reseau_interne):
    """Une requête vers l'extérieur doit échouer depuis le réseau interne (SPEC §4.6).

    Le contrôle est fait à variables de proxy VIDÉES : sans cela, curl échouerait
    parce qu'il ne joint pas le proxy du poste de fabrication, ce qui ne prouverait
    rien sur l'isolation du réseau. Un témoin sur le réseau par défaut montre que
    la même requête, elle, établit bien une connexion.
    """
    image = _image_sonde(config)
    sans_proxy = ["--env", "HTTPS_PROXY=", "--env", "HTTP_PROXY=",
                  "--env", "https_proxy=", "--env", "http_proxy="]
    commande = (
        "curl -sS -m 10 -o /dev/null -w 'code=%{http_code}' https://1.1.1.1 2>&1"
        "; echo \" rc=$?\""
    )

    interne = _podman(
        "run", "--rm", "--network", reseau_interne, *sans_proxy,
        "--entrypoint", "sh", image, "-c", commande, timeout=90,
    )
    temoin = _podman(
        "run", "--rm", *sans_proxy, "--entrypoint", "sh", image, "-c", commande, timeout=90,
    )

    assert "rc=0" not in interne.stdout, (
        f"le réseau « --internal » laisse sortir : {interne.stdout.strip()!r}"
    )
    assert "rc=7" in interne.stdout, (
        "sur un réseau interne, la connexion doit échouer faute de route (rc=7) ; "
        f"obtenu : {interne.stdout.strip()!r}"
    )
    # Témoin : sur le réseau par défaut la connexion s'établit (rc différent de 7).
    assert "rc=7" not in temoin.stdout, (
        "le témoin sur le réseau par défaut échoue lui aussi faute de route : "
        f"le contrôle ne prouve donc rien. Obtenu : {temoin.stdout.strip()!r}"
    )


# --------------------------------------------------------------------------
# Cloisonnement : ce que le stagiaire ne doit PAS voir
#
# Les deux contrôles ci-dessous portent sur des défauts réels, trouvés en
# relecture P8 : les corrigés étaient chargés dans le Space de formation, et le
# rôle « stagiaire » lisait le jeu de l'épreuve toute la journée. Ils sont menés
# avec le COMPTE DU STAGIAIRE : les mener avec « elastic » ne prouverait rien.
# --------------------------------------------------------------------------

def test_le_stagiaire_ne_lit_pas_le_jeu_de_l_epreuve(es_stagiaire, config, lab_demarre):
    """Sinon il prépare ses réponses toute la journée et l'épreuve ne mesure rien."""
    motif = str(config.valeur("epreuve.data_view_motif"))
    # Un index NOMMÉ explicitement doit être refusé. Le joker, lui, ne lève pas
    # d'erreur : il se résout silencieusement à rien — d'où les deux contrôles.
    index_nomme = motif.replace("*", "ids.alert")
    r = es_stagiaire.get(f"{es_stagiaire.base}/{index_nomme}/_count", timeout=30)
    assert r.status_code == 403, (
        f"« {index_nomme} » répond {r.status_code} au stagiaire, 403 attendu"
    )

    r = es_stagiaire.get(f"{es_stagiaire.base}/{motif}/_count", timeout=30)
    assert r.status_code == 200
    assert r.json()["count"] == 0, (
        f"le joker « {motif} » rapporte {r.json()['count']} documents au stagiaire"
    )

    # Et le jeu du parcours, lui, doit rester lisible : un cloisonnement qui
    # bloque tout n'est pas un cloisonnement, c'est une panne.
    parcours = str(config.valeur("donnees.data_view_motif"))
    r = es_stagiaire.get(f"{es_stagiaire.base}/{parcours}/_count", timeout=30)
    assert r.status_code == 200 and r.json()["count"] > 0, (
        "le stagiaire ne lit plus le jeu du parcours"
    )


def test_le_stagiaire_ne_voit_ni_les_corriges_ni_l_epreuve(kbn_stagiaire, config, lab_demarre):
    """Les Spaces visibles du stagiaire : la formation, et le Space voisin.

    « corriges » porte les tableaux de bord dont les titres donnent les réponses
    de M3 et M4 ; « epreuve » n'est ouvert qu'au moment de l'évaluation, par
    « make epreuve-ouvrir ».
    """
    r = kbn_stagiaire.get(f"{kbn_stagiaire.base}/api/spaces/space", timeout=30)
    assert r.status_code == 200, f"liste des Spaces : HTTP {r.status_code}"
    visibles = {s["id"] for s in r.json()}

    formation = str(config.valeur("formation.space_id"))
    assert formation in visibles, "le stagiaire ne voit pas son propre Space"
    assert "reseau" in visibles, (
        "le Space « reseau » est invisible : M3-E5 et M5-E3 n'ont plus de cible"
    )
    interdits = visibles & {"corriges", "epreuve"}
    assert not interdits, f"Spaces visibles à tort par le stagiaire : {sorted(interdits)}"


def test_aucun_corrige_dans_le_space_de_formation(kbn_stagiaire, config, lab_demarre):
    """Un corrigé visible dès la connexion, c'est la journée entière dévoilée."""
    formation = str(config.valeur("formation.space_id"))
    r = kbn_stagiaire.get(
        f"{kbn_stagiaire.base}/s/{formation}/api/saved_objects/_find"
        "?type=dashboard&per_page=100",
        timeout=30,
    )
    assert r.status_code == 200, f"recherche d'objets : HTTP {r.status_code}"
    titres = [o["attributes"].get("title", "") for o in r.json()["saved_objects"]]
    suspects = [
        t for t in titres
        if "corrig" in t.lower() or t in ("Santé de la collecte", "Vue IDS")
    ]
    assert not suspects, f"corrigés présents dans le Space de formation : {suspects}"
