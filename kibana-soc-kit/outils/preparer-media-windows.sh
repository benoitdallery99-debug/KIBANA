#!/usr/bin/env bash
# outils/preparer-media-windows.sh — constitue, sur un poste CONNECTÉ, le dossier
# à emporter vers un PC Windows hors ligne (docs/INSTALLATION_WINDOWS_HORS_LIGNE.md).
#
# À lancer dans une Ubuntu WSL2 connectée où le kit tourne déjà (le lab doit
# avoir tiré ses images : « make lab-images »). Produit, par défaut dans
# C:\kit-media :
#   - l'Ubuntu 24.04 officielle pour WSL, et son empreinte publiée par Canonical ;
#   - les paquets système du kit, tirés DE CETTE MÊME Ubuntu, et leur index apt ;
#   - l'installateur de WSL (MSI), pour un PC où WSL n'est pas encore installé ;
#   - l'archive du kit (images, wheels, guide, PDF) et son empreinte ;
#   - comptes.env : les mots de passe des comptes Kibana, JAMAIS dans le dépôt ;
#   - le script d'installation hors ligne, le guide (LISEZMOI.html et .md),
#     VERSION.txt, et MEDIA.SHA256.
#
# Mots de passe : KIT_MDP_STAGIAIRE et KIT_MDP_FORMATEUR s'ils sont fournis,
# sinon demandés. Laissés vides, comptes.env n'est pas écrit et les mots de
# passe se fixeront à l'installation.
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
# La version de WSL mesurée sur le poste où la procédure a été éprouvée.
WSL_VERSION="${KIT_WSL_VERSION:-2.6.1}"
WSL_MSI="wsl.${WSL_VERSION}.0.x64.msi"
WSL_URL="https://github.com/microsoft/WSL/releases/download/${WSL_VERSION}/${WSL_MSI}"
PY="${KIT_PYTHON:-$RACINE/.venv/bin/python}"

titre() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

mkdir -p "$MEDIA" "$TRAVAIL"

titre "1/6 Ubuntu 24.04 pour WSL, image officielle"
curl -fsSL "$UBUNTU_URL/SHA256SUMS" | grep " \*\{0,1\}$ROOTFS\$" > "$TRAVAIL/$ROOTFS.sha256"
# Vérifié seulement s'il est déjà là : sinon « sha256sum -c » affichait
# « FAILED open or read » avant même le téléchargement — mesuré au premier
# usage réel, et de quoi inquiéter pour rien.
if [ ! -f "$TRAVAIL/$ROOTFS" ] \
   || ! (cd "$TRAVAIL" && sha256sum -c --quiet "$ROOTFS.sha256" >/dev/null 2>&1); then
  echo "  téléchargement de $ROOTFS (~340 Mo)…"
  curl -fL --progress-bar -o "$TRAVAIL/$ROOTFS" "$UBUNTU_URL/$ROOTFS"
  (cd "$TRAVAIL" && sha256sum -c --quiet "$ROOTFS.sha256")
fi
echo "  empreinte conforme à celle publiée par Canonical"
cp "$TRAVAIL/$ROOTFS" "$TRAVAIL/$ROOTFS.sha256" "$MEDIA/"

titre "2/6 Installateur de WSL ${WSL_VERSION}, pour un PC qui ne l'a pas encore"
if [ ! -f "$TRAVAIL/$WSL_MSI" ]; then
  echo "  téléchargement de $WSL_MSI (~250 Mo)…"
  curl -fL --progress-bar -o "$TRAVAIL/$WSL_MSI.part" "$WSL_URL"
  mv "$TRAVAIL/$WSL_MSI.part" "$TRAVAIL/$WSL_MSI"
fi
# Microsoft ne publie pas d'empreinte à côté du MSI : celle-ci est MESURÉE au
# téléchargement. La preuve d'origine est la signature Authenticode, que le
# guide fait contrôler sous Windows (Get-AuthenticodeSignature).
(cd "$TRAVAIL" && sha256sum "$WSL_MSI" > "$WSL_MSI.sha256")
cp "$TRAVAIL/$WSL_MSI" "$TRAVAIL/$WSL_MSI.sha256" "$MEDIA/"
echo "  $WSL_MSI copié ($(du -h "$MEDIA/$WSL_MSI" | cut -f1))"

titre "3/6 Paquets système, tirés de cette même Ubuntu"
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

titre "4/6 Archive du kit"
if [ ! -f dist/guide.html ]; then make guide; fi
make package
ARCHIVE="$(find dist -maxdepth 1 -name 'kit-formation-kibana-*.tar.gz' -printf '%T@ %p\n' \
  | sort -rn | head -1 | cut -d' ' -f2)"
rm -f "$MEDIA"/kit-formation-kibana-*.tar.gz "$MEDIA"/kit-formation-kibana-*.tar.gz.sha256
cp "$ARCHIVE" "$ARCHIVE.sha256" "$MEDIA/"
(cd "$MEDIA" && sha256sum -c --quiet "$(basename "$ARCHIVE").sha256")
echo "  $(basename "$ARCHIVE") copiée, empreinte conforme"

titre "5/6 Comptes Kibana : comptes.env"
lire_mdp() {  # $1 : variable, $2 : identifiant affiché
  local v="${!1:-}" confirmation
  if [ -z "$v" ] && [ -t 0 ]; then
    # Tout ce qui s'affiche part sur stderr : la fonction est appelée par
    # « $(...) », et un « echo » sur stdout finirait DANS le mot de passe.
    while :; do
      read -rsp "  Mot de passe de « $2 » (6 caractères au moins, Entrée : plus tard) : " v; echo >&2
      [ -z "$v" ] && break
      if [ "${#v}" -lt 6 ]; then echo "  Refusé : Elasticsearch exige 6 caractères au moins." >&2; continue; fi
      read -rsp "  Retapez-le : " confirmation; echo >&2
      [ "$v" = "$confirmation" ] && break
      echo "  Les deux saisies diffèrent." >&2
    done
  fi
  if [ -n "$v" ] && [ "${#v}" -lt 6 ]; then
    echo "  ERREUR : $1 fait ${#v} caractères, Elasticsearch en exige 6 au moins." >&2
    exit 1
  fi
  printf '%s' "$v"
}
LOGIN_STAGIAIRE="$("$PY" -c 'from outils import conf; print(conf.identifiant("stagiaire"))')"
LOGIN_FORMATEUR="$("$PY" -c 'from outils import conf; print(conf.identifiant("formateur"))')"
MDP_S="$(lire_mdp KIT_MDP_STAGIAIRE "$LOGIN_STAGIAIRE")"
MDP_F="$(lire_mdp KIT_MDP_FORMATEUR "$LOGIN_FORMATEUR")"
rm -f "$MEDIA/comptes.env"
if [ -n "$MDP_S" ] || [ -n "$MDP_F" ]; then
  {
    echo "# Mots de passe des comptes Kibana. Ce fichier voyage sur le support, JAMAIS"
    echo "# dans le dépôt, qui est public. Lu par : make mots-de-passe DEPUIS=<ce fichier>"
    echo "# Identifiants : « $LOGIN_STAGIAIRE » (stagiaire), « $LOGIN_FORMATEUR » (formateur)."
    [ -n "$MDP_S" ] && echo "KIT_MDP_STAGIAIRE=$MDP_S"
    [ -n "$MDP_F" ] && echo "KIT_MDP_FORMATEUR=$MDP_F"
  } > "$MEDIA/comptes.env"
  echo "  comptes.env écrit (identifiants « $LOGIN_STAGIAIRE » et « $LOGIN_FORMATEUR »)"
else
  echo "  aucun mot de passe fourni : ils se fixeront à l'installation (make mots-de-passe)"
fi

titre "6/6 Guide, version et empreintes du support"
cp outils/installer-prerequis-horsligne.sh "$MEDIA/"
cp docs/INSTALLATION_WINDOWS_HORS_LIGNE.md "$MEDIA/LISEZMOI.md"
"$PY" - "$MEDIA/LISEZMOI.md" "$MEDIA/LISEZMOI.html" <<'PYEOF'
import sys, markdown
source, cible = sys.argv[1], sys.argv[2]
corps = markdown.markdown(open(source, encoding="utf-8").read(),
                          extensions=["tables", "fenced_code"])
style = """body{font:16px/1.6 system-ui,sans-serif;max-width:52rem;margin:2rem auto;padding:0 1rem;color:#1b1a17;background:#faf8f4}
h1,h2,h3{font-family:Georgia,serif;line-height:1.2}h2{border-bottom:2px solid #1a5a8a;padding-bottom:.3rem;margin-top:2.5rem}
pre{background:#1b1a17;color:#faf8f4;padding:.8rem 1rem;border-radius:3px;overflow-x:auto;font-size:15px}
code{font-family:ui-monospace,Consolas,monospace}p code,li code,td code{background:#ece7dc;padding:0 .25rem;border-radius:3px}
table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #c9c2b4;padding:.35rem .55rem;text-align:left;vertical-align:top}
th{background:#ece7dc}blockquote{border-left:4px solid #9c2a1a;margin:1rem 0;padding:.2rem 1rem;background:#fbeeec}"""
page = ("<!doctype html><html lang=\"fr\"><head><meta charset=\"utf-8\">"
        "<title>Installer le kit Kibana hors ligne</title><style>" + style
        + "</style></head><body>" + corps + "</body></html>")
open(cible, "w", encoding="utf-8").write(page)
PYEOF
{
  echo "Kit de formation Kibana pour analystes SOC — support d'installation hors ligne"
  echo
  echo "Version du kit      : $(basename "$ARCHIVE" .tar.gz)"
  echo "Commit              : $(git -C "$RACINE" describe --always --dirty 2>/dev/null || echo inconnu) ($(git -C "$RACINE" log -1 --format=%cs 2>/dev/null || echo ?))"
  echo "Elastic Stack       : $("$PY" -c 'from outils import conf; print(conf.version())') (licence Basic)"
  echo "Image elasticsearch : $(sed -n 's/^elasticsearch:[[:space:]]*//p' lab/images.yaml)"
  echo "Image kibana        : $(sed -n 's/^kibana:[[:space:]]*//p' lab/images.yaml)"
  echo "Ubuntu pour WSL     : $ROOTFS"
  echo "WSL                 : $WSL_VERSION ($WSL_MSI)"
  echo "Paquets système     : $(grep -c '^Package:' "$MEDIA/debs/Packages")"
  echo "Comptes Kibana      : « $LOGIN_STAGIAIRE » (stagiaire), « $LOGIN_FORMATEUR » (formateur)"
  echo "Support préparé le  : $(date '+%Y-%m-%d %H:%M')"
} > "$MEDIA/VERSION.txt"
# Écrit hors du support puis recopié : le fichier ne doit pas s'empreinter lui-même.
EMPREINTES="$(mktemp)"
(cd "$MEDIA" && find . -type f ! -name MEDIA.SHA256 -print0 | sort -z \
  | xargs -0 sha256sum) > "$EMPREINTES"
# « cat » et non « mv » : sur /mnt/c, mv ne peut pas recopier date et droits et
# le signalait par deux « Operation not permitted », sans conséquence mais
# alarmants — relevé au premier usage réel, sur un PC Windows.
cat "$EMPREINTES" > "$MEDIA/MEDIA.SHA256" && rm -f "$EMPREINTES"
echo "  $(wc -l < "$MEDIA/MEDIA.SHA256") fichiers empreintés dans MEDIA.SHA256"

printf '\n\033[32mSupport prêt\033[0m : %s (%s)\n' "$MEDIA" "$(du -sh "$MEDIA" | cut -f1)"
cat "$MEDIA/VERSION.txt"
