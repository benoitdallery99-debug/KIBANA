#!/usr/bin/env bash
# lab/epreuve.sh — ouvre ou ferme l'épreuve pratique pour le compte « stagiaire ».
#
# Le jeu de l'épreuve (logs-*-epreuve) et son Space ne sont PAS lisibles par le
# rôle « stagiaire ». S'ils l'étaient, un stagiaire pourrait préparer ses réponses
# pendant toute la journée de formation, et l'évaluation ne mesurerait plus rien.
#
# L'ouverture ajoute le rôle « stagiaire-epreuve » au compte ; la fermeture le
# retire. Les deux opérations sont idempotentes.
#
#   bash lab/epreuve.sh ouvrir
#   bash lab/epreuve.sh fermer

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

URL_ES="${KIT_URL_ES:-http://localhost:${KIT_PORT_ES:-9200}}"
PY="${KIT_PYTHON:-$RACINE/.venv/bin/python}"
# Identifiant lu dans kit.config.yaml, comme partout ailleurs.
COMPTE="$("$PY" -c 'from outils import conf; print(conf.identifiant("stagiaire"))')"
ROLE_EPREUVE="stagiaire-epreuve"

action="${1:-}"
case "$action" in
  ouvrir|fermer) ;;
  *) echo "usage: bash lab/epreuve.sh {ouvrir|fermer}" >&2; exit 2 ;;
esac

set -a
# .env est engendré à l'installation : shellcheck ne peut pas le suivre.
# shellcheck disable=SC1091
. ./.env
set +a

if [ "$action" = "ouvrir" ]; then
  roles='["stagiaire","'"$ROLE_EPREUVE"'"]'
  message="Épreuve OUVERTE : « $COMPTE » lit désormais le jeu de l'épreuve et voit le Space « epreuve »."
else
  roles='["stagiaire"]'
  message="Épreuve FERMÉE : « $COMPTE » ne lit plus que le jeu du parcours."
fi

# « PUT _security/user » REMPLACE l'utilisateur : relevé en lab, un corps sans
# « full_name » vide le champ. Le mot de passe, lui, est conservé quand il est
# omis (la réponse renvoie « created: false »). Il n'existe pas de sous-ressource
# « /_roles » : elle répond 400.
corps="{\"roles\":$roles,\"full_name\":\"Stagiaire\"}"

sortie="$(curl -s -w '\n%{http_code}' -X PUT \
  -u "elastic:$ELASTIC_PASSWORD" -H 'Content-Type: application/json' \
  "$URL_ES/_security/user/$COMPTE" -d "$corps" 2>/dev/null || true)"
code="$(printf '%s' "$sortie" | tail -n1)"

if [ "$code" != "200" ]; then
  echo "ÉCHEC : Elasticsearch a répondu ${code:-aucun code}" >&2
  printf '%s\n' "$sortie" | sed '$d' >&2
  echo "Le lab est-il démarré ?  make lab-up" >&2
  exit 1
fi

echo "$message"

# On affiche l'état constaté, pas l'état supposé : une commande qui affirme sans
# relire est exactement ce que ce kit interdit.
curl -s -u "elastic:$ELASTIC_PASSWORD" "$URL_ES/_security/user/$COMPTE" \
  | sed -n 's/.*"roles":\[\([^]]*\)\].*/  rôles relus : [\1]/p'
echo
