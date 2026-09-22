#!/usr/bin/env bash
# lab/reset.sh — repart à neuf : le lab est détruit, reconstruit, et les données
# sont réengendrées pour se terminer à l'instant présent.
#
# À lancer entre deux sessions de formation. Sans cela, le jeu de données garde
# la date de son dernier chargement : les exercices bâtis sur « les sept derniers
# jours » ne trouvent plus rien, et le scénario S6 (source muette) ne se lit plus,
# puisqu'il se mesure par rapport à la fin de la fenêtre.
#
# DESTRUCTIF : le volume d'Elasticsearch est supprimé. Tout ce qu'un stagiaire a
# enregistré dans Kibana — recherches, visualisations, tableaux de bord — disparaît.
# D'où la confirmation, qu'on peut lever avec « --oui » pour un usage scripté.

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

PY="${KIT_PYTHON:-$RACINE/.venv/bin/python}"
NOM_POD="${KIT_NOM_POD:-kibana-soc-lab}"
VOLUME="${NOM_POD}-es-data"

confirme="${KIT_SANS_CONFIRMATION:-0}"
for arg in "$@"; do
  case "$arg" in
    --oui|-y) confirme=1 ;;
    *) echo "usage: bash lab/reset.sh [--oui]" >&2; exit 2 ;;
  esac
done

titre() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

if [ "$confirme" != "1" ]; then
  printf '\033[33mCette opération détruit le volume « %s ».\033[0m\n' "$VOLUME"
  echo "Tout le travail enregistré dans Kibana sera perdu, sans récupération possible."
  printf 'Taper « oui » pour continuer : '
  read -r reponse
  if [ "$reponse" != "oui" ]; then
    echo "Abandon : rien n'a été touché."
    exit 1
  fi
fi

titre "1/4 Arrêt du lab"
bash lab/lab-down.sh

titre "2/4 Suppression du volume de données"
# Le pod vient d'être retiré : le volume n'est plus référencé, « rm » simple suffit.
# On n'emploie pas « -f », qui détruirait aussi les conteneurs qui l'utilisent —
# une erreur déjà faite dans ce kit, et qui avait emporté le lab entier.
if podman volume exists "$VOLUME" 2>/dev/null; then
  # On ne se fie PAS au code de retour : relevé en lab, « podman volume rm »
  # supprime bien le volume puis sort en erreur s'il ne retrouve pas le fichier
  # de verrou (« freeing lock for volume ... : no such file or directory »),
  # ce qui arrive quand /run a été vidé sous lui. Sous « set -e », le script
  # s'arrêtait là, le lab à l'arrêt et la réinitialisation à moitié faite.
  # On regarde donc l'ÉTAT, pas le code de retour.
  sortie="$(podman volume rm "$VOLUME" 2>&1)" || true
  if podman volume exists "$VOLUME" 2>/dev/null; then
    echo "  ÉCHEC : le volume « $VOLUME » est toujours là." >&2
    echo "  podman a répondu : $sortie" >&2
    echo "  Un conteneur l'utilise-t-il encore ?  podman ps -a" >&2
    exit 1
  fi
  echo "  volume « $VOLUME » supprimé."
  case "$sortie" in
    *"freeing lock"*)
      echo "  (podman a signalé un verrou introuvable ; le volume est bien parti.)" ;;
  esac
else
  echo "  volume « $VOLUME » absent — rien à supprimer."
fi

titre "3/4 Redémarrage et réinitialisation"
bash lab/lab-up.sh

titre "4/5 Rechargement des données, réancrées sur maintenant"
"$PY" data/generateur/engendrer.py --jeu formation
"$PY" data/generateur/engendrer.py --jeu epreuve
# Les corrigés vivent dans le Space « corriges » et sont repartis avec le volume :
# on les recharge, sans quoi le formateur n'a plus de quoi débriefer M3 et M4.
"$PY" corriges/construire.py

titre "5/5 Reconstruction du guide sur les nouvelles réponses"
# README.md prescrit « make lab-reset » avant chaque séance. Sans cette étape,
# chaque séance commençait donc avec un guide dont les empreintes dataient de
# la séance précédente : le stagiaire saisissait la bonne réponse et se la
# voyait refuser. Le HTML seul suffit — c'est lui qui valide.
"$PY" guide/build.py

printf '\n\033[32mLab remis à neuf.\033[0m  Données réancrées sur %s.\n' "$(date '+%Y-%m-%d %H:%M')"
printf 'L'"'"'épreuve pratique reste FERMÉE : « make epreuve-ouvrir » le moment venu.\n\n'
