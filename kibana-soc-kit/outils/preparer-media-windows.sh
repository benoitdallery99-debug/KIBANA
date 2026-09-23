#!/usr/bin/env bash
# outils/preparer-media-windows.sh — constitue, sur un poste CONNECTÉ, le dossier
# à emporter vers un PC Windows hors ligne (docs/INSTALLATION_WINDOWS_HORS_LIGNE.md).
#
# À lancer dans une Ubuntu WSL2 connectée où le kit tourne déjà (le lab doit
# avoir tiré ses images : « make lab-images »). Produit, par défaut dans
# C:\kit-media :
#   - l'Ubuntu 24.04 officielle pour WSL, et son empreinte publiée par Canonical ;
#   - les paquets système du kit, tirés DE CETTE MÊME Ubuntu, et leur index apt ;
#   - l'archive du kit (images, wheels, guide, PDF) et son empreinte ;
#   - le script d'installation hors ligne, un LISEZMOI, et MEDIA.SHA256.
#
# MESURÉ le 23/09 : les paquets doivent venir de l'image même qu'on importera.
# Tirés d'une autre image Ubuntu 24.04 (celle de Docker), il en fallait 118 ;
# tirés de l'image WSL, 39 — et un paquet tiré ailleurs peut RÉTROGRADER une
# bibliothèque déjà présente. Et ils s'installent par un dépôt local indexé :
# « dpkg -i debs/*.deb » échouait hors ligne sur les pré-dépendances.
set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

MEDIA="${1:-/mnt/c/kit-media}"
UBUNTU_URL="${KIT_UBUNTU_WSL:-https://cloud-images.ubuntu.com/wsl/releases/24.04/current}"
ROOTFS="ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz"
PAQUETS="podman uidmap netavark aardvark-dns passt slirp4netns catatonit conmon \
fuse-overlayfs golang-github-containers-common make curl gawk iproute2 iptables python3-venv"
TRAVAIL="${XDG_CACHE_HOME:-$HOME/.cache}/kit-media"

titre() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

mkdir -p "$MEDIA" "$TRAVAIL"

titre "1/4 Ubuntu 24.04 pour WSL, image officielle"
curl -fsSL "$UBUNTU_URL/SHA256SUMS" | grep " \*\{0,1\}$ROOTFS\$" > "$TRAVAIL/$ROOTFS.sha256"
if ! (cd "$TRAVAIL" && sha256sum -c --quiet "$ROOTFS.sha256" 2>/dev/null); then
  echo "  téléchargement de $ROOTFS (~340 Mo)…"
  curl -fL --progress-bar -o "$TRAVAIL/$ROOTFS" "$UBUNTU_URL/$ROOTFS"
  (cd "$TRAVAIL" && sha256sum -c --quiet "$ROOTFS.sha256")
fi
echo "  empreinte conforme à celle publiée par Canonical"
cp "$TRAVAIL/$ROOTFS" "$TRAVAIL/$ROOTFS.sha256" "$MEDIA/"

titre "2/4 Paquets système, tirés de cette même Ubuntu"
podman import -q "$TRAVAIL/$ROOTFS" localhost/kit-media-ubuntu:24.04 >/dev/null
rm -rf "$TRAVAIL/debs" && mkdir -p "$TRAVAIL/debs"
podman run --rm -e http_proxy -e https_proxy -e HTTP_PROXY -e HTTPS_PROXY \
  -e PAQUETS="$PAQUETS" -v "$TRAVAIL/debs:/debs" localhost/kit-media-ubuntu:24.04 bash -c '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  # shellcheck disable=SC2086
  apt-get install -y -qq --download-only -o Dir::Cache::archives=/debs $PAQUETS >/dev/null
  apt-get install -y -qq apt-utils >/dev/null
  cd /debs && rm -rf partial lock && apt-ftparchive packages . > Packages
  echo "  $(grep -c ^Package: Packages) paquets indexés"'
echo "$PAQUETS" > "$TRAVAIL/debs/paquets.txt"
podman rmi -f localhost/kit-media-ubuntu:24.04 >/dev/null 2>&1 || true
rm -rf "$MEDIA/debs" && cp -r "$TRAVAIL/debs" "$MEDIA/debs"

titre "3/4 Archive du kit"
if [ ! -f dist/guide.html ]; then make guide; fi
make package
ARCHIVE="$(find dist -maxdepth 1 -name 'kit-formation-kibana-*.tar.gz' -printf '%T@ %p\n' \
  | sort -rn | head -1 | cut -d' ' -f2)"
rm -f "$MEDIA"/kit-formation-kibana-*.tar.gz "$MEDIA"/kit-formation-kibana-*.tar.gz.sha256
cp "$ARCHIVE" "$ARCHIVE.sha256" "$MEDIA/"
(cd "$MEDIA" && sha256sum -c --quiet "$(basename "$ARCHIVE").sha256")
echo "  $(basename "$ARCHIVE") copiée, empreinte conforme"

titre "4/4 Installateur, LISEZMOI et empreintes du support"
cp outils/installer-prerequis-horsligne.sh "$MEDIA/"
cp docs/INSTALLATION_WINDOWS_HORS_LIGNE.md "$MEDIA/LISEZMOI.md"
# Écrit hors du support puis déplacé : le fichier ne doit pas s'empreinter lui-même.
EMPREINTES="$(mktemp)"
(cd "$MEDIA" && find . -type f ! -name MEDIA.SHA256 -print0 | sort -z \
  | xargs -0 sha256sum) > "$EMPREINTES"
mv "$EMPREINTES" "$MEDIA/MEDIA.SHA256"
echo "  $(wc -l < "$MEDIA/MEDIA.SHA256") fichiers empreintés dans MEDIA.SHA256"

printf '\n\033[32mSupport prêt\033[0m : %s (%s)\n' "$MEDIA" "$(du -sh "$MEDIA" | cut -f1)"
