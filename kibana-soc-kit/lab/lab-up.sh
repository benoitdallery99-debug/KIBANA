#!/usr/bin/env bash
# lab/lab-up.sh — démarre le lab et l'initialise. Idempotent.
#
# Enchaînement : pré-vol → rendu du pod → podman kube play → attente
# d'Elasticsearch → mot de passe kibana_system → attente de Kibana → init.
# Aucun téléchargement : les images doivent déjà être dans le magasin local.

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

PY="${KIT_PYTHON:-$RACINE/.venv/bin/python}"
NOM_POD="${KIT_NOM_POD:-kibana-soc-lab}"
URL_ES="${KIT_URL_ES:-http://localhost:${KIT_PORT_ES:-9200}}"
URL_KIBANA="${KIT_URL_KIBANA:-http://localhost:${KIT_PORT_KIBANA:-5601}}"

# Délais d'attente, en secondes. Généreux : un premier démarrage sur un poste
# modeste peut être lent, et échouer trop tôt donnerait un diagnostic faux.
ATTENTE_ES=300
ATTENTE_KIBANA=420

titre() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

titre "1/6 Pré-vol"
bash lab/preflight.sh

titre "2/6 Rendu du pod"
"$PY" lab/rendre_pod.py

titre "3/6 Démarrage du pod"
pod_preexistant=0
if podman pod exists "$NOM_POD" 2>/dev/null; then
  pod_preexistant=1
  echo "  pod « $NOM_POD » déjà présent — démarrage ignoré (lab-up est idempotent)."
  podman pod start "$NOM_POD" >/dev/null 2>&1 || true
else
  podman kube play lab/generated/pod.yaml
fi

set -a
# .env est engendré à l'installation : shellcheck ne peut pas le suivre.
# shellcheck disable=SC1091
. ./.env
set +a

titre "4/6 Attente d'Elasticsearch"
debut=$(date +%s)
while :; do
  # L'échec d'une tentative est normal tant que le service démarre : on neutralise
  # le code de retour, sinon « set -e » interromprait l'attente dès le premier essai.
  etat="$(curl -s -u "elastic:$ELASTIC_PASSWORD" "$URL_ES/_cluster/health" 2>/dev/null \
    | sed -n 's/.*"status":"\([a-z]*\)".*/\1/p' || true)"
  if [ "$etat" = "green" ] || [ "$etat" = "yellow" ]; then
    echo "  Elasticsearch prêt (santé « $etat ») en $(( $(date +%s) - debut ))s."
    break
  fi
  if [ $(( $(date +%s) - debut )) -ge "$ATTENTE_ES" ]; then
    echo "  ÉCHEC : Elasticsearch n'est pas prêt après ${ATTENTE_ES}s." >&2
    echo "  Journal :  podman logs ${NOM_POD}-elasticsearch" >&2
    if [ "$pod_preexistant" = "1" ]; then
      # Constaté : après un redémarrage brutal de la machine hôte, podman peut
      # annoncer le pod « Running » alors que ses conteneurs sont morts.
      # « pod start » ne relève alors rien, sans le dire.
      echo >&2
      echo "  Le pod existait déjà au lancement. Si podman l'annonce démarré" >&2
      echo "  alors que rien ne répond, ses conteneurs sont morts sans qu'il" >&2
      echo "  l'ait enregistré. Recréez-le — le volume de données est conservé :" >&2
      echo "      make lab-down && make lab-up" >&2
    fi
    exit 1
  fi
  sleep 3
done

titre "5/6 Compte de service kibana_system"
# Kibana ne peut pas se connecter avec « elastic » depuis la 8.0 : son mot de passe
# est fixé ici. L'index .security peut n'être pas encore alloué juste après le
# démarrage : on réessaie (constaté en lab, HTTP 503 unavailable_shards_exception).
debut=$(date +%s)
while :; do
  code="$(curl -s -o /dev/null -w '%{http_code}' -X POST \
    -u "elastic:$ELASTIC_PASSWORD" -H 'Content-Type: application/json' \
    "$URL_ES/_security/user/kibana_system/_password" \
    -d "{\"password\":\"$KIBANA_SYSTEM_PASSWORD\"}" 2>/dev/null || true)"
  [ "$code" = "200" ] && { echo "  mot de passe kibana_system fixé."; break; }
  if [ $(( $(date +%s) - debut )) -ge 120 ]; then
    echo "  ÉCHEC : impossible de fixer le mot de passe kibana_system (dernier code $code)." >&2
    exit 1
  fi
  sleep 3
done

titre "6/6 Attente de Kibana puis initialisation"
debut=$(date +%s)
while :; do
  niveau="$(curl -s "$URL_KIBANA/api/status" 2>/dev/null \
    | sed -n 's/.*"overall":{"level":"\([a-z]*\)".*/\1/p' || true)"
  if [ "$niveau" = "available" ]; then
    echo "  Kibana disponible en $(( $(date +%s) - debut ))s."
    break
  fi
  if [ $(( $(date +%s) - debut )) -ge "$ATTENTE_KIBANA" ]; then
    echo "  ÉCHEC : Kibana n'est pas disponible après ${ATTENTE_KIBANA}s (dernier niveau « $niveau »)." >&2
    echo "  Journal :  podman logs ${NOM_POD}-kibana" >&2
    exit 1
  fi
  sleep 3
done

"$PY" lab/init/init.py

COMPTES="$("$PY" -c 'from outils import conf; print("« " + conf.identifiant("stagiaire") + " » (stagiaire) et « " + conf.identifiant("formateur") + " » (formateur)")')"
printf '\n\033[32mLab prêt.\033[0m  Kibana : %s\n  Comptes : %s — mots de passe dans .env, modifiables par « make mots-de-passe ».\n\n' "$URL_KIBANA" "$COMPTES"
