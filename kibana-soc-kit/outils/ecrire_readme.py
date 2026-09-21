# ruff: noqa: E501
# Les lignes longues de ce fichier sont des lignes de tableau Markdown, qui font
# partie du texte livré : les couper casserait les tableaux des README.
"""Écrit les deux README de l'archive livrable — SPEC P7.

- README.md            : démarrage formateur en TROIS commandes ;
- INSTALLATION.md      : installation hors ligne, pas à pas, sur un poste vierge.

Les versions, ports et noms viennent de kit.config.yaml : rien n'est écrit en dur.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf

DEMARRAGE = """\
# Kit de formation Kibana pour analystes SOC

Parcours pratique de {duree} minutes sur un lab reproductible, entièrement hors
ligne. Elastic Stack **{version}**, licence **Basic**, interface **{locale}**.

## Démarrage, en trois commandes

```bash
./installer.sh      # charge les images et installe les dépendances (une fois)
make lab-up         # démarre Elasticsearch et Kibana, et initialise le Space
make data           # engendre et charge les données de la séance
```

Kibana répond ensuite sur <http://localhost:{port}>.
Les identifiants sont dans `.env`, créé au premier démarrage et jamais partagé.

Ouvrez `guide.html` dans un navigateur : c'est le parcours du stagiaire. Il
fonctionne seul, sans réseau, sans serveur.

## Avant chaque session

```bash
make lab-reset
```

Les données sont en **fenêtre glissante** : elles se terminent à l'instant du
chargement. Sans réinitialisation, la dernière séance vieillit et les scénarios
qui reposent sur « depuis deux heures » perdent leur sens.

## Ce que contient l'archive

| Chemin | Contenu |
|---|---|
| `guide.html` | Le parcours du stagiaire, autonome, un seul fichier |
| `guide.pdf` | Le même parcours, imprimable, solutions en annexe |
| `fiche-memo.pdf` | A4 recto verso, à imprimer pour chaque stagiaire |
| `formateur/` | Déroulé minuté, matrice, quiz, épreuve pratique, corrigés |
| `corriges/` | Les deux tableaux de bord de référence, en JSON et en ndjson |
| `lab/` | Le lab podman : pod, pré-vol, initialisation |
| `data/` | Le générateur de données synthétiques |
| `parcours/` | La source des modules |
| `images/` | Les images de conteneurs, à charger avec `podman load` |
| `wheels/` | Les dépendances Python, pour une installation sans réseau |
| `verif/` | La suite de vérification (`make verif`) |
| `docs/` | Spécification, capacités qualifiées, journal, note de conception |

## Vérifier que tout est en place

```bash
make verif
```

## Avertissement sur les données

{avertissement}
"""

INSTALLATION = """\
# Installation hors ligne, pas à pas

Ce kit ne télécharge **jamais** rien. Tout ce dont il a besoin est dans
l'archive. Ces instructions supposent un poste sans accès à Internet.

## 1. Vérifier les empreintes

```bash
sha256sum -c SHA256SUMS
```

Toutes les lignes doivent afficher « Réussi ». Une seule ligne en échec, et
l'archive est à retélécharger : ne poursuivez pas.

## 2. Prérequis du poste

| Élément | Minimum | Pourquoi |
|---|---|---|
| podman | 4.4 | Le lab est lancé par `podman kube play` |
| Mémoire libre | 6 Go | Heap Elasticsearch de 2 Go, plus Kibana |
| Espace disque | 10 Go | Images, index et données |
| `vm.max_map_count` | 262144 | Exigence d'Elasticsearch |
| Python | 3.11 | Générateur, construction, vérifications |

Le pré-vol contrôle tout cela et **dit quoi faire** en cas de manque :

```bash
bash lab/preflight.sh
```

Il n'exécute jamais de commande `sudo` : il l'affiche, et vous décidez.

### Sous macOS ou Windows

podman tourne dans une machine virtuelle. Les réglages se font **dans cette VM** :

```bash
podman machine stop
podman machine set --memory 8192
podman machine start
podman machine ssh 'sudo sysctl -w vm.max_map_count=262144'
```

## 3. Installer

```bash
./installer.sh
```

Le script charge les images de conteneurs depuis `images/`, crée
l'environnement Python à partir des wheels de `wheels/`, et ne joint aucun
réseau. Il est relançable sans effet de bord.

## 4. Démarrer

```bash
make lab-up
make data
```

Au premier démarrage, `.env` est créé : il contient les mots de passe engendrés
pour ce poste. Il n'est pas dans l'archive et ne doit pas en sortir.

## 5. Contrôler

```bash
make verif-lab
make verif-donnees
```

## En cas d'échec

| Symptôme | Cause la plus fréquente | Remède |
|---|---|---|
| `make lab-up` s'arrête au pré-vol | Un prérequis manque | Le pré-vol affiche la commande exacte |
| Cluster en `red`, shards non alloués | Disque trop occupé | Libérez de l'espace ; le lab tolère un disque plein en pourcentage mais pas un disque sans place réelle |
| Kibana reste `unavailable` | Elasticsearch pas encore prêt | Attendez ; `podman logs {pod}-kibana` dit où il en est |
| Le lab ne répond pas sur un réseau isolé | `bridge-nf-call-iptables` à 1 | `sudo sysctl -w net.bridge.bridge-nf-call-iptables=0` |
| Image absente au démarrage | `podman load` non fait | Relancez `./installer.sh` |

## Désinstaller

```bash
make lab-down
podman volume rm {pod}-es-data
podman rmi $(podman images -q)
```
"""

INSTALLEUR = """\
#!/usr/bin/env bash
# installer.sh — installe le kit sur un poste hors ligne. Idempotent.
set -euo pipefail
RACINE="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$RACINE"

echo "== Vérification des empreintes =="
if command -v sha256sum >/dev/null 2>&1 && [ -f SHA256SUMS ]; then
  sha256sum -c --quiet SHA256SUMS && echo "  empreintes conformes"
else
  echo "  (sha256sum indisponible : contrôle ignoré)"
fi

echo "== Chargement des images de conteneurs =="
for archive in images/*.tar; do
  [ -f "$archive" ] || continue
  echo "  podman load < $archive"
  podman load -i "$archive" >/dev/null
done
podman images --format '  {{{{.Repository}}}}:{{{{.Tag}}}}' | sort -u

echo "== Environnement Python =="
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if [ -d wheels ] && [ -n "$(ls -A wheels 2>/dev/null)" ]; then
  # --no-index : aucune connexion à PyPI, même si le réseau existe.
  .venv/bin/pip install --quiet --no-index --find-links wheels -r exigences.txt
  echo "  dépendances installées depuis wheels/"
else
  echo "  AVERTISSEMENT : wheels/ est vide ; les dépendances doivent déjà être installées." >&2
fi

echo
echo "Installation terminée. Suite :"
echo "    make lab-up"
echo "    make data"
"""


def main() -> int:
    cible = Path(sys.argv[1]) if len(sys.argv) > 1 else conf.RACINE / "dist"
    cible.mkdir(parents=True, exist_ok=True)

    import json
    manifeste_chemin = conf.RACINE / "data" / "manifest.json"
    avertissement = "Données entièrement synthétiques."
    duree = 345
    if manifeste_chemin.exists():
        manifeste = json.loads(manifeste_chemin.read_text(encoding="utf-8"))
        avertissement = manifeste["avertissement"]

    variables = {
        "version": conf.version(),
        "locale": conf.valeur("kibana.locale"),
        "port": conf.PORT_KIBANA,
        "pod": conf.NOM_POD,
        "duree": duree,
        "avertissement": avertissement,
    }

    (cible / "README.md").write_text(DEMARRAGE.format(**variables), encoding="utf-8")
    (cible / "INSTALLATION.md").write_text(INSTALLATION.format(**variables), encoding="utf-8")
    installeur = cible / "installer.sh"
    installeur.write_text(INSTALLEUR.format(**variables), encoding="utf-8")
    installeur.chmod(0o755)

    print(f"  README.md, INSTALLATION.md et installer.sh écrits dans {cible.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
