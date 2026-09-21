#!/usr/bin/env bash
# outils/empaqueter.sh — construit l'archive livrable, hors ligne par construction.
#
# Le livrable ne télécharge JAMAIS rien (CLAUDE.md, SPEC §3.1). Tout ce dont il a
# besoin voyage avec lui : les images de conteneurs, les dépendances Python en
# wheels, les polices, le guide, les PDF, les corrigés, les scripts.

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

PY="${KIT_PYTHON:-$RACINE/.venv/bin/python}"
DEPOT="${KIT_DEPOT_IMAGES:-mirror.gcr.io/library}"
VERSION="$(sed -n 's/^  version:[[:space:]]*"\{0,1\}\([0-9.]*\)"\{0,1\}.*/\1/p' kit.config.yaml | head -1)"
HORODATAGE="$(date -u +%Y%m%d)"
NOM="kit-formation-kibana-${VERSION}-${HORODATAGE}"
ETAPE="$RACINE/dist/$NOM"

titre() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

titre "1/6 Guide et documents"
if [ ! -f dist/guide.html ]; then
  echo "  dist/guide.html absent — lancez « make guide » d'abord." >&2
  exit 1
fi

rm -rf "$ETAPE"
mkdir -p "$ETAPE"/{lab,data,parcours,corriges,guide,captures,verif,formateur,docs,images,wheels,outils}

cp dist/guide.html "$ETAPE/"
for pdf in dist/*.pdf; do [ -f "$pdf" ] && cp "$pdf" "$ETAPE/"; done
echo "  guide et PDF copiés"

titre "2/6 Sources du kit"
cp kit.config.yaml Makefile exigences.txt pyproject.toml CLAUDE.md "$ETAPE/"
cp -r lab/* "$ETAPE/lab/" 2>/dev/null || true
rm -rf "$ETAPE/lab/generated"
cp -r data/generateur data/manifest.json "$ETAPE/data/" 2>/dev/null || true
cp -r parcours/* "$ETAPE/parcours/" 2>/dev/null || true
cp -r corriges/* "$ETAPE/corriges/" 2>/dev/null || true
cp -r guide/* "$ETAPE/guide/" 2>/dev/null || true
cp -r captures/* "$ETAPE/captures/" 2>/dev/null || true
cp -r verif/* "$ETAPE/verif/" 2>/dev/null || true
cp -r formateur/* "$ETAPE/formateur/" 2>/dev/null || true
cp -r outils/* "$ETAPE/outils/" 2>/dev/null || true
cp docs/*.md "$ETAPE/docs/" 2>/dev/null || true
cp docs/*.json "$ETAPE/docs/" 2>/dev/null || true
find "$ETAPE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
# Le manifeste de l'épreuve reste côté formateur : il porte les réponses.
rm -f "$ETAPE/data/manifest-epreuve.json"
echo "  sources copiées"

titre "3/6 Images de conteneurs"
# podman save : les images voyagent avec l'archive, et le lab les charge avec
# « podman load ». Aucun registre n'est joint à l'exécution.
for image in elasticsearch kibana; do
  cible="$ETAPE/images/${image}.tar"
  if [ -f "$cible" ]; then echo "  $image déjà présent"; continue; fi
  echo "  podman save $image:$VERSION …"
  podman save --format docker-archive -o "$cible" "$DEPOT/${image}:${VERSION}"
  printf '    %s : %s Mo\n' "$image" "$(( $(stat -c%s "$cible") / 1024 / 1024 ))"
done

titre "4/6 Dépendances Python"
# Vendorisées en wheels : l'installation sur la cible ne joint pas PyPI.
"$PY" -m pip download --quiet --dest "$ETAPE/wheels" -r exigences.txt 2>&1 | tail -2 || {
  echo "  AVERTISSEMENT : téléchargement des wheels impossible (réseau ?)." >&2
  echo "  L'archive reste utilisable si Python et ses dépendances sont déjà en place." >&2
}
echo "  $(find "$ETAPE/wheels" -name '*.whl' -o -name '*.tar.gz' 2>/dev/null | wc -l) paquet(s)"

titre "5/6 README d'installation"
"$PY" outils/ecrire_readme.py "$ETAPE"

titre "6/6 Empreintes et archive"
# Les empreintes sont écrites hors de l'arborescence parcourue, puis déplacées :
# écrire le fichier dans le répertoire qu'on est en train de lire le ferait
# s'empreinter lui-même, ou pas, selon l'ordre de parcours.
EMPREINTES="$(mktemp)"
(
  cd "$ETAPE"
  find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$EMPREINTES"
mv "$EMPREINTES" "$ETAPE/SHA256SUMS"
echo "  $(wc -l < "$ETAPE/SHA256SUMS") fichier(s) empreintés"

ARCHIVE="$RACINE/dist/${NOM}.tar.gz"
tar -czf "$ARCHIVE" -C "$RACINE/dist" "$NOM"
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

printf '\n\033[32mArchive prête\033[0m : %s (%s Mo)\n' \
  "dist/${NOM}.tar.gz" "$(( $(stat -c%s "$ARCHIVE") / 1024 / 1024 ))"
printf 'Empreinte : %s\n\n' "$(cut -d' ' -f1 "$ARCHIVE.sha256")"
