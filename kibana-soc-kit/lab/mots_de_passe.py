"""Fixe les mots de passe des comptes de connexion à Kibana.

    make mots-de-passe                                   # les demande
    make mots-de-passe DEPUIS=/mnt/c/kit-media/comptes.env  # les lit dans un fichier

Deux comptes : celui du stagiaire et celui du formateur, dont les identifiants
sont dans kit.config.yaml (« stagiaire » et « admin » par défaut). Les mots de
passe, eux, ne sont jamais dans le dépôt — il est public. Ils vivent dans .env,
et ce script les y écrit.

Si le lab tourne, le changement est appliqué tout de suite ; sinon, il le sera
au prochain « make lab-up », qui recrée les comptes depuis .env. Un mot de
passe laissé vide n'est pas changé. Aucun mot de passe n'est jamais affiché.

Le fichier lu par DEPUIS contient, une par ligne :
    KIT_MDP_STAGIAIRE=...
    KIT_MDP_FORMATEUR=...
"""

from __future__ import annotations

import argparse
import getpass
import importlib.util
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf

ENV = conf.RACINE / ".env"
CLES = {"stagiaire": ("KIT_MDP_STAGIAIRE", "STAGIAIRE_PASSWORD"),
        "formateur": ("KIT_MDP_FORMATEUR", "FORMATEUR_PASSWORD")}


def lire_fichier(chemin: Path) -> dict[str, str]:
    if not chemin.is_file():
        raise SystemExit(f"Fichier introuvable : {chemin}")
    valeurs: dict[str, str] = {}
    for ligne in chemin.read_text(encoding="utf-8-sig").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, val = ligne.partition("=")
        valeurs[cle.strip()] = val.strip()
    return valeurs


def demander(role: str) -> str:
    login = conf.identifiant(role)
    while True:
        mdp = getpass.getpass(f"Nouveau mot de passe de « {login} » (Entrée : inchangé) : ")
        if not mdp:
            return ""
        if len(mdp) < conf.MDP_LONGUEUR_MIN:
            print(f"  Refusé : {len(mdp)} caractères, Elasticsearch en exige au moins "
                  f"{conf.MDP_LONGUEUR_MIN}.")
            continue
        if getpass.getpass("  Retapez-le : ") != mdp:
            print("  Les deux saisies diffèrent, recommencez.")
            continue
        return mdp


def assurer_env() -> None:
    """Crée .env s'il manque, par le même code que le rendu du pod."""
    if ENV.exists():
        return
    spec = importlib.util.spec_from_file_location(
        "rendre_pod", conf.RACINE / "lab" / "rendre_pod.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.assurer_env()


def ecrire_env(nouveaux: dict[str, str]) -> None:
    lignes = ENV.read_text(encoding="utf-8").splitlines()
    for i, ligne in enumerate(lignes):
        cle = ligne.partition("=")[0].strip()
        if cle in nouveaux:
            lignes[i] = f"{cle}={nouveaux.pop(cle)}"
    lignes += [f"{cle}={val}" for cle, val in nouveaux.items()]
    ENV.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    ENV.chmod(0o600)


def appliquer(login: str, mdp: str) -> str:
    """Change le mot de passe dans Elasticsearch si le lab répond."""
    try:
        r = requests.post(
            f"{conf.url_es()}/_security/user/{login}/_password",
            json={"password": mdp}, auth=conf.auth_elastic(), timeout=15,
        )
    except requests.RequestException:
        return "lab arrêté : sera appliqué au prochain « make lab-up »"
    if r.status_code == 200:
        return "appliqué"
    # MESURÉ : sur un compte inexistant, Elasticsearch répond 400 « user must
    # exist in order to change password », et non 404. C'est le cas d'un lab
    # installé avant le renommage du compte du formateur : le mot de passe est
    # déjà dans .env, et « make lab-up » créera le compte avec lui.
    if r.status_code == 404 or (r.status_code == 400 and "user must exist" in r.text):
        return ("compte pas encore créé : il le sera, avec ce mot de passe, "
                "au prochain « make lab-up »")
    raise SystemExit(f"  Elasticsearch a refusé le changement pour « {login} » : "
                     f"HTTP {r.status_code} {r.text[:200]}")


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--depuis", type=Path, default=None,
                   help="fichier KIT_MDP_STAGIAIRE=… / KIT_MDP_FORMATEUR=…")
    args = a.parse_args()

    source = lire_fichier(args.depuis) if args.depuis else dict(os.environ)
    choisis: dict[str, str] = {}
    for role, (variable, _) in CLES.items():
        mdp = source.get(variable, "")
        if not mdp and args.depuis is None and sys.stdin.isatty():
            mdp = demander(role)
        if not mdp:
            continue
        if len(mdp) < conf.MDP_LONGUEUR_MIN:
            raise SystemExit(f"{variable} : {len(mdp)} caractères, or Elasticsearch en "
                             f"exige au moins {conf.MDP_LONGUEUR_MIN}. Rien n'a été changé.")
        choisis[role] = mdp

    if not choisis:
        print("Aucun mot de passe fourni : rien n'a été changé.")
        return 0

    assurer_env()
    ecrire_env({CLES[role][1]: mdp for role, mdp in choisis.items()})
    for role, mdp in choisis.items():
        login = conf.identifiant(role)
        print(f"  [OK]  « {login} » ({role}) : {appliquer(login, mdp)}")
    print("Mots de passe enregistrés dans .env (droits 600).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
