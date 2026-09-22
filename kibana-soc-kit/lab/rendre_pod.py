"""Engendre lab/generated/pod.yaml à partir de lab/pod.yaml.tmpl et de .env.

Les secrets (mots de passe, clés de chiffrement) sont créés au premier appel dans
.env, qui est gitignoré : aucun secret n'entre dans le dépôt (CLAUDE.md).
Les images sont épinglées par digest, relevé une fois et consigné dans
lab/images.yaml, pour que le lab soit reproductible à l'octet près.
"""

from __future__ import annotations

import argparse
import os
import secrets as _secrets
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf

GABARIT = conf.RACINE / "lab" / "pod.yaml.tmpl"
SORTIE = conf.RACINE / "lab" / "generated" / "pod.yaml"
IMAGES = conf.RACINE / "lab" / "images.yaml"
ENV = conf.RACINE / ".env"

HEAP = "2g"  # documenté dans docs/PLAN.md et le guide formateur


def mot_de_passe() -> str:
    """Mot de passe engendré : 32 caractères d'alphabet sûr pour un .env."""
    return _secrets.token_urlsafe(24)


def cle() -> str:
    """Clé de chiffrement Kibana : 32 octets en hexadécimal (64 caractères)."""
    return _secrets.token_hex(32)


def assurer_env() -> dict[str, str]:
    """Crée .env au premier appel, puis le relit. Idempotent : ne réécrit jamais."""
    if not ENV.exists():
        lignes = [
            "# Secrets du lab, engendrés à l'installation. NE JAMAIS COMMITER.",
            "# Supprimez ce fichier et relancez « make lab-up » pour tout régénérer",
            "# (le lab sera alors reconstruit de zéro).",
            f"ELASTIC_PASSWORD={mot_de_passe()}",
            f"KIBANA_SYSTEM_PASSWORD={mot_de_passe()}",
            f"FORMATEUR_PASSWORD={mot_de_passe()}",
            f"STAGIAIRE_PASSWORD={mot_de_passe()}",
            f"CLE_SAVED_OBJECTS={cle()}",
            f"CLE_REPORTING={cle()}",
            f"CLE_SECURITY={cle()}",
        ]
        ENV.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        ENV.chmod(0o600)
        print(f"[rendre_pod] secrets engendrés dans {ENV.name} (droits 600)")
    return conf.secrets()


def digest(image: str) -> str:
    """Renvoie la référence par digest d'une image déjà présente localement."""
    r = subprocess.run(
        ["podman", "inspect", image, "--format", "{{index .RepoDigests 0}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise SystemExit(
            f"Image absente du magasin local : {image}\n"
            "Le lab ne télécharge rien à l'exécution. Chargez les images livrées avec\n"
            "    podman load -i images/elasticsearch.tar && podman load -i images/kibana.tar\n"
            "ou, sur la chaîne de fabrication, lancez « make lab-images »."
        )
    return r.stdout.strip()


def existe_localement(reference: str) -> bool:
    """L'image est-elle résolvable TELLE QUELLE dans le magasin local ?"""
    return subprocess.run(
        ["podman", "image", "exists", reference], capture_output=True, check=False
    ).returncode == 0


def images() -> dict[str, str]:
    """Relit lab/images.yaml, ou le crée depuis le magasin local au premier appel.

    PIÈGE, mesuré : « podman save --format docker-archive » resérialise l'image,
    et « podman load » lui redonne un digest de manifeste DIFFÉRENT de celui du
    registre. Sur la chaîne de fabrication, où les images viennent d'un « pull »,
    le digest épinglé ici résout ; sur un poste hors ligne, où elles viennent du
    tar livré, il ne résout pas — et « imagePullPolicy: Never » interdit d'aller
    le chercher. Le lab ne démarrait donc pas sur une installation hors ligne
    neuve, alors qu'il démarrait sur les deux machines qui l'avaient construit.
    Aucun des 121 contrôles ne le voyait, faute d'en avoir jamais chargé un tar.

    L'épinglage par digest est conservé — c'est lui qui rend le lab reproductible
    à l'octet près — mais il est désormais VÉRIFIÉ contre le magasin local, et
    réancré sur lui quand il n'y résout pas.
    """
    v = conf.version()
    if IMAGES.exists():
        d = yaml.safe_load(IMAGES.read_text(encoding="utf-8"))
        if d.get("version") != v:
            print(f"[rendre_pod] lab/images.yaml concerne {d.get('version')}, "
                  f"or stack.version = {v} : relevé à neuf")
        else:
            absents = [nom for nom in ("elasticsearch", "kibana")
                       if d.get(nom) and not existe_localement(d[nom])]
            if not absents:
                return d
            print(f"[rendre_pod] digest épinglé introuvable dans le magasin local "
                  f"({', '.join(absents)}) : images chargées depuis un tar livré, "
                  f"dont le manifeste est resérialisé. Réancrage sur le magasin.")

    depot = os.environ.get("KIT_DEPOT_IMAGES", "mirror.gcr.io/library")
    d = {
        "version": v,
        "commentaire": (
            "Digests relevés sur la chaîne de fabrication. docker.elastic.co étant bloqué par "
            "la politique d'egress du poste de fabrication, les images officielles ont été "
            "obtenues par le miroir mirror.gcr.io ; le digest de configuration est identique à "
            "celui publié par Docker Hub. Voir docs/JOURNAL.md, décision D4."
        ),
        "elasticsearch": digest(f"{depot}/elasticsearch:{v}"),
        "kibana": digest(f"{depot}/kibana:{v}"),
    }
    IMAGES.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("[rendre_pod] digests relevés dans lab/images.yaml")
    return d


def arguments() -> argparse.Namespace:
    a = argparse.ArgumentParser(description="Engendre le pod du lab depuis son gabarit.")
    a.add_argument("--nom", default=conf.NOM_POD, help="nom du pod (défaut : %(default)s)")
    a.add_argument(
        "--sortie", default=None, help="fichier de sortie (défaut : lab/generated/pod.yaml)"
    )
    a.add_argument(
        "--sans-hostports",
        action="store_true",
        help=(
            "retire la publication des ports vers l'hôte. Nécessaire pour jouer le pod sur "
            "un réseau podman « --internal », qui ne publie pas de ports (SPEC §4.6)."
        ),
    )
    return a.parse_args()


def main() -> int:
    args = arguments()
    sortie = Path(args.sortie) if args.sortie else SORTIE
    env = assurer_env()
    img = images()
    remplacements = {
        "__NOM_POD__": args.nom,
        "__IMAGE_ES__": img["elasticsearch"],
        "__IMAGE_KIBANA__": img["kibana"],
        "__PORT_ES__": str(conf.PORT_ES),
        "__PORT_KIBANA__": str(conf.PORT_KIBANA),
        "__MDP_ELASTIC__": env["ELASTIC_PASSWORD"],
        "__MDP_KIBANA_SYSTEM__": env["KIBANA_SYSTEM_PASSWORD"],
        "__CLE_SAVED_OBJECTS__": env["CLE_SAVED_OBJECTS"],
        "__CLE_REPORTING__": env["CLE_REPORTING"],
        "__CLE_SECURITY__": env["CLE_SECURITY"],
        "__LOCALE__": str(conf.valeur("kibana.locale")),
        "__HEAP__": HEAP,
    }
    texte = GABARIT.read_text(encoding="utf-8")
    for cle_, val in remplacements.items():
        texte = texte.replace(cle_, val)

    restants = sorted({m for m in texte.split() if m.startswith("__") and m.endswith("__")})
    if restants:
        raise SystemExit(f"gabarit incomplet, marqueurs non substitués : {restants}")

    if args.sans_hostports:
        # Un réseau « --internal » ne publie pas de ports vers l'hôte : on les retire.
        # Le rendu passe alors par un aller-retour YAML, qui perd les commentaires ;
        # ce n'est pas gênant, cette variante ne sert qu'aux vérifications.
        docs = [d for d in yaml.safe_load_all(texte) if d]
        for d in docs:
            if d.get("kind") != "Pod":
                continue
            for c in d["spec"]["containers"]:
                for port in c.get("ports", []):
                    port.pop("hostPort", None)
        texte = yaml.safe_dump_all(docs, allow_unicode=True, sort_keys=False)

    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(texte, encoding="utf-8")
    sortie.chmod(0o600)

    # Contrôle : le rendu doit être du YAML valide, et décrire un PVC puis un Pod.
    docs = [d for d in yaml.safe_load_all(sortie.read_text(encoding="utf-8")) if d]
    genres = [d.get("kind") for d in docs]
    if genres != ["PersistentVolumeClaim", "Pod"]:
        raise SystemExit(f"rendu inattendu : {genres}")

    # « --sortie » accepte un chemin hors du dépôt : relative_to() levait alors
    # une ValueError APRÈS que le fichier eut été écrit — un échec annoncé sur
    # un travail réussi.
    try:
        nom_affiche = sortie.relative_to(conf.RACINE)
    except ValueError:
        nom_affiche = sortie
    print(f"[rendre_pod] {nom_affiche} engendré — pod « {args.nom} », "
          f"Elasticsearch et Kibana {conf.version()}, "
          f"locale {conf.valeur('kibana.locale')}, heap {HEAP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
