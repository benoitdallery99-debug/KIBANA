"""Fixtures communes aux suites de vérification.

Toutes les suites lisent kit.config.yaml : aucun paramètre n'est écrit en dur.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf


@pytest.fixture(scope="session")
def config():
    return conf


@pytest.fixture(scope="session")
def auth():
    return conf.auth_elastic()


@pytest.fixture(scope="session")
def es(auth):
    """Session HTTP vers Elasticsearch, authentifiée."""
    s = requests.Session()
    s.auth = auth
    s.headers.update({"Content-Type": "application/json"})
    s.base = conf.url_es()
    return s


@pytest.fixture(scope="session")
def kbn(auth):
    """Session HTTP vers Kibana, authentifiée, avec l'en-tête anti-CSRF."""
    s = requests.Session()
    s.auth = auth
    s.headers.update({"kbn-xsrf": "true", "Content-Type": "application/json"})
    s.base = conf.url_kibana()
    return s


@pytest.fixture(scope="session")
def manifeste(config):
    """Manifeste du jeu du parcours, partagé par toutes les suites.

    Il était défini à l'identique dans trois fichiers de test ; une quatrième
    copie aurait suivi. Une seule définition, ici.
    """
    chemin = config.RACINE / "data" / "manifest.json"
    if not chemin.exists():
        pytest.skip("NON EXÉCUTÉ : data/manifest.json absent. Lancez « make data ».")
    return json.loads(chemin.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def es_stagiaire():
    """Session HTTP vers Elasticsearch AVEC LE COMPTE DU STAGIAIRE.

    Sert à vérifier ce qu'il ne doit PAS pouvoir lire. Un contrôle de
    cloisonnement mené avec le compte « elastic » ne prouverait rien.
    """
    s = requests.Session()
    s.auth = (conf.identifiant("stagiaire"), conf.secrets()["STAGIAIRE_PASSWORD"])
    s.base = conf.url_es()
    return s


@pytest.fixture(scope="session")
def kbn_stagiaire():
    """Session HTTP vers Kibana avec le compte du stagiaire."""
    s = requests.Session()
    s.auth = (conf.identifiant("stagiaire"), conf.secrets()["STAGIAIRE_PASSWORD"])
    s.headers.update({"kbn-xsrf": "true", "Content-Type": "application/json"})
    s.base = conf.url_kibana()
    return s


@pytest.fixture(scope="session")
def lab_demarre(es):
    """Ignore proprement les suites qui exigent un lab démarré, plutôt que d'échouer.

    Un contrôle non exécuté doit être signalé comme NON EXÉCUTÉ, avec sa raison,
    jamais comme PASSÉ (CLAUDE.md).
    """
    try:
        r = es.get(f"{es.base}/_cluster/health", timeout=10)
        r.raise_for_status()
    except Exception as exc:
        pytest.skip(
            f"NON EXÉCUTÉ : lab injoignable sur {es.base} ({exc}). Lancez « make lab-up »."
        )
    return True
