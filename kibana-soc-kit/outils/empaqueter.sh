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
#
# PIÈGE, relevé en instruisant l'installation sur un poste hors ligne : un
# « pip download » sans --platform produit les wheels DE LA MACHINE DE
# FABRICATION. Trois d'entre elles portaient « manylinux_x86_64 » ET « cp311 » :
# l'archive n'était installable que sur Linux x86_64 avec CPython 3.11 très
# exactement. Sur WSL2 Ubuntu 24.04, qui livre 3.12, l'installation échouait.
# On déclare donc les cibles, on les télécharge toutes, et on ÉCRIT ce qui est
# couvert — pour que l'installateur le sache avant de partir en salle blanche,
# et non devant un pip qui refuse.
#
# Windows natif n'est volontairement pas une cible : le kit est piloté par des
# scripts bash et un Makefile, et podman y tourne de toute façon dans une VM.
# Sous Windows, tout se passe dans WSL2, qui est un Linux x86_64.
CIBLES="${KIT_CIBLES_WHEELS:-manylinux_2_17_x86_64/manylinux2014_x86_64:3.11 manylinux_2_17_x86_64/manylinux2014_x86_64:3.12 macosx_11_0_arm64:3.11 macosx_11_0_arm64:3.12}"

couvertes=""
for cible in $CIBLES; do
  plateformes="${cible%%:*}"
  version_py="${cible##*:}"
  args=""
  # Une cible peut nommer plusieurs étiquettes de plateforme compatibles.
  ancien_ifs="$IFS"; IFS='/'
  for p in $plateformes; do args="$args --platform $p"; done
  IFS="$ancien_ifs"
  # shellcheck disable=SC2086
  if "$PY" -m pip download --quiet --dest "$ETAPE/wheels" \
      --only-binary=:all: --python-version "$version_py" $args \
      -r exigences.txt >/dev/null 2>&1; then
    echo "  [OK]  ${plateformes%%/*} / CPython $version_py"
    couvertes="$couvertes${couvertes:+, }${plateformes%%/*} cp${version_py}"
  else
    echo "  [--]  ${plateformes%%/*} / CPython $version_py : aucune roue complète" >&2
  fi
done

# Les paquets sans roue publiée pour une cible donnée arriveraient en source :
# on complète par un téléchargement sans contrainte, qui les capte pour la
# plateforme de fabrication au moins.
"$PY" -m pip download --quiet --dest "$ETAPE/wheels" -r exigences.txt >/dev/null 2>&1 || {
  echo "  AVERTISSEMENT : téléchargement des wheels impossible (réseau ?)." >&2
  echo "  L'archive reste utilisable si Python et ses dépendances sont déjà en place." >&2
}

{
  echo "Plateformes couvertes par wheels/ :"
  echo "  ${couvertes:-aucune (téléchargement contraint en échec)}"
  echo
  echo "Une wheel dont le nom porte « cp311 » ou « manylinux » ne s'installe QUE"
  echo "sur la version de Python et la plateforme correspondantes. Vérifiez avant"
  echo "de partir hors ligne :"
  echo "    python3 --version        # doit être l'une des versions ci-dessus"
  echo "    python3 -c 'import sysconfig; print(sysconfig.get_platform())'"
  echo
  echo "Windows natif n'est pas une cible : sous Windows, le kit s'installe dans"
  echo "WSL2, qui est un Linux x86_64. Voir INSTALLATION.md."
} > "$ETAPE/wheels/CIBLES.txt"

echo "  $(find "$ETAPE/wheels" -name '*.whl' -o -name '*.tar.gz' 2>/dev/null | wc -l) paquet(s), $(du -sh "$ETAPE/wheels" | cut -f1)"

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
# MESURÉ : « sha256sum "$ARCHIVE" » écrit le chemin ABSOLU de la machine de
# fabrication. Sur le poste cible, « sha256sum -c » cherche alors un fichier
# qui n'existe pas et échoue — sur une archive pourtant intacte. Le nom seul,
# écrit depuis le répertoire qui contient l'archive, se vérifie partout.
(cd "$(dirname "$ARCHIVE")" && sha256sum "$(basename "$ARCHIVE")") > "$ARCHIVE.sha256"

printf '\n\033[32mArchive prête\033[0m : %s (%s Mo)\n' \
  "dist/${NOM}.tar.gz" "$(( $(stat -c%s "$ARCHIVE") / 1024 / 1024 ))"
printf 'Empreinte : %s\n\n' "$(cut -d' ' -f1 "$ARCHIVE.sha256")"
