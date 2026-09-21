#!/usr/bin/env bash
# lab/lab-down.sh — arrête et retire le pod du lab.
# Le volume de données est conservé : « make lab-reset » s'en charge.
set -euo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"
NOM_POD="${KIT_NOM_POD:-kibana-soc-lab}"

if [ -f lab/generated/pod.yaml ]; then
  podman kube down lab/generated/pod.yaml >/dev/null 2>&1 || true
fi
podman pod rm -f "$NOM_POD" >/dev/null 2>&1 || true
echo "Lab arrêté. Le volume « ${NOM_POD}-es-data » est conservé (make lab-reset pour repartir à neuf)."
