#!/usr/bin/env bash
# installer-prerequis-horsligne.sh — installe SANS RÉSEAU les paquets système du
# kit dans une Ubuntu 24.04 importée par « wsl --import ». Voyage sur le support
# préparé par outils/preparer-media-windows.sh, à côté de debs/.
#
# MESURÉ le 23/09 dans une copie neuve de l'image WSL officielle, sans réseau :
# « dpkg -i debs/*.deb » échoue (ordre alphabétique contre pré-dépendances), et
# « apt-get install ./debs/*.deb » aussi (noms de fichiers à époque). Un dépôt
# local indexé laisse apt résoudre l'ordre : 0 paquet non configuré.
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" != 0 ]; then
  echo "À lancer en root. Une distribution importée par « wsl --import » s'ouvre en root ;" >&2
  echo "sinon : sudo bash $0" >&2
  exit 1
fi
if [ ! -f "$ICI/debs/Packages" ] || [ ! -f "$ICI/debs/paquets.txt" ]; then
  echo "debs/Packages ou debs/paquets.txt absent à côté de ce script : support incomplet." >&2
  exit 1
fi

echo "== Dépôt local =="
# Copié sur le disque Linux : apt lit mal un dépôt posé sur /mnt/c.
rm -rf /var/cache/kit-debs && cp -r "$ICI/debs" /var/cache/kit-debs
# Les sources en ligne sont mises de côté : hors ligne, « apt-get update » y
# échouerait, bruyamment et pour rien. Elles restent récupérables.
if [ -d /etc/apt/sources.list.d ] && [ ! -d /etc/apt/sources.list.d.en-ligne ]; then
  mv /etc/apt/sources.list.d /etc/apt/sources.list.d.en-ligne
  mkdir /etc/apt/sources.list.d
fi
if [ -f /etc/apt/sources.list ]; then mv /etc/apt/sources.list /etc/apt/sources.list.en-ligne; fi
echo "deb [trusted=yes] file:/var/cache/kit-debs ./" > /etc/apt/sources.list.d/kit-local.list
apt-get update -qq

echo "== Installation =="
# shellcheck disable=SC2046
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $(cat /var/cache/kit-debs/paquets.txt) >/dev/null
non_configures="$(dpkg -l | grep -cvE '^ii|^Desired|^\||^\+' || true)"
echo "  paquets non configurés : $non_configures"

echo "== Contrôle =="
podman --version
make --version | head -1
python3 --version
python3 -m venv --help >/dev/null && echo "venv disponible"
[ "$non_configures" = 0 ] || { echo "ÉCHEC : des paquets ne sont pas configurés." >&2; exit 1; }
echo
echo "Prérequis installés. Suite : extraire l'archive du kit et lancer ./installer.sh"
