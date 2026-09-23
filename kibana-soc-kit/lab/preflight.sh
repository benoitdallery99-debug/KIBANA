#!/usr/bin/env bash
# lab/preflight.sh — contrôles préalables au démarrage du lab.
#
# Principe : chaque échec dit QUOI FAIRE, pas seulement ce qui ne va pas (SPEC §4.2).
# Aucune commande « sudo » n'est exécutée ici : elle est affichée, l'humain décide
# (CLAUDE.md). Le script sort en 1 au premier blocage, 0 si tout est réunis.

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT_ES="${KIT_PORT_ES:-9200}"
PORT_KIBANA="${KIT_PORT_KIBANA:-5601}"

# Seuils, documentés dans docs/PLAN.md et le guide formateur.
MIN_MAX_MAP_COUNT=262144
MIN_RAM_GO=6
MIN_DISQUE_GO=10
# Sous macOS et Windows, l'hôte ne porte que le dépôt et l'environnement
# Python : les images et les index vivent dans la machine virtuelle podman.
MIN_DISQUE_HOTE_GO=3
MIN_PYTHON=3.11
MIN_PODMAN="4.4"

bloquants=0
avertissements=0

titre() { printf '\n\033[1m%s\033[0m\n' "$1"; }
ok()    { printf '  \033[32m[OK]\033[0m    %s\n' "$1"; }
alerte(){ printf '  \033[33m[ATTN]\033[0m  %s\n' "$1"; avertissements=$((avertissements + 1)); }
echec() { printf '  \033[31m[ÉCHEC]\033[0m %s\n' "$1"; bloquants=$((bloquants + 1)); }
faire() { printf '           \033[36m→ %s\033[0m\n' "$1"; }

version_ge() { printf '%s\n%s\n' "$2" "$1" | sort -V -C; }

titre "1. Runtime de conteneurs"
if ! command -v podman >/dev/null 2>&1; then
  echec "podman est introuvable."
  faire "Installez podman : https://podman.io/docs/installation"
  faire "Le lab est lancé par « podman kube play » : docker n'est pas prévu."
else
  v="$(podman --version | awk '{print $3}')"
  if version_ge "$v" "$MIN_PODMAN"; then
    ok "podman $v (minimum $MIN_PODMAN)"
  else
    echec "podman $v est trop ancien (minimum $MIN_PODMAN pour « kube play »)."
    faire "Mettez podman à jour."
  fi
fi

titre "2. Paramètres noyau"
if [ -r /proc/sys/vm/max_map_count ]; then
  mmc="$(cat /proc/sys/vm/max_map_count)"
  if [ "$mmc" -ge "$MIN_MAX_MAP_COUNT" ]; then
    ok "vm.max_map_count = $mmc (minimum $MIN_MAX_MAP_COUNT)"
  else
    echec "vm.max_map_count = $mmc, or Elasticsearch exige au moins $MIN_MAX_MAP_COUNT."
    faire "Pour la session courante :  sudo sysctl -w vm.max_map_count=$MIN_MAX_MAP_COUNT"
    faire "Pour rendre le réglage permanent :"
    faire "  echo 'vm.max_map_count=$MIN_MAX_MAP_COUNT' | sudo tee /etc/sysctl.d/99-elasticsearch.conf"
    faire "Ces commandes ne sont PAS exécutées automatiquement : à vous de les lancer."
  fi
else
  alerte "vm.max_map_count illisible : vous n'êtes probablement pas sous Linux."
  faire "Sous macOS ou Windows, podman tourne dans une machine virtuelle."
  faire "Réglez le paramètre DANS cette VM :"
  faire "  podman machine ssh 'sudo sysctl -w vm.max_map_count=$MIN_MAX_MAP_COUNT'"
fi

titre "3. Mémoire"
if [ -r /proc/meminfo ]; then
  ram_ko="$(awk '/MemAvailable/ {print $2}' /proc/meminfo)"
  ram_go=$((ram_ko / 1024 / 1024))
  if [ "$ram_go" -ge "$MIN_RAM_GO" ]; then
    ok "${ram_go} Go de mémoire disponible (minimum ${MIN_RAM_GO} Go)"
  else
    echec "${ram_go} Go disponibles, or le lab en demande ${MIN_RAM_GO} (heap Elasticsearch 2 Go + Kibana)."
    faire "Fermez des applications, ou augmentez la mémoire de la VM podman :"
    faire "  podman machine stop && podman machine set --memory 8192 && podman machine start"
  fi
else
  # Hors Linux, podman tourne dans une machine virtuelle : c'est SA mémoire qui
  # compte, pas celle de l'hôte. Un Mac de 16 Go avec une VM réglée à 2 Go ne
  # fera pas tourner Elasticsearch, et l'inverse est vrai aussi. On interroge
  # donc la VM plutôt que de renvoyer l'humain à son propre jugement.
  vm_mo="$(podman machine inspect --format '{{.Resources.Memory}}' 2>/dev/null \
           | tr -dc '0-9' | head -c 9)"
  if [ -n "$vm_mo" ] && [ "$vm_mo" -gt 0 ] 2>/dev/null; then
    vm_go=$((vm_mo / 1024))
    if [ "$vm_go" -ge "$MIN_RAM_GO" ]; then
      ok "${vm_go} Go alloués à la machine podman (minimum ${MIN_RAM_GO} Go)"
    else
      echec "la machine podman n'a que ${vm_go} Go, or le lab en demande ${MIN_RAM_GO}."
      faire "podman machine stop && podman machine set --memory 8192 && podman machine start"
    fi
  else
    alerte "Mémoire disponible non mesurable sur ce système."
    faire "Assurez-vous d'avoir au moins ${MIN_RAM_GO} Go libres, dont 2 Go pour le heap Elasticsearch."
  fi
fi

titre "4. Espace disque"
# PIÈGE RELEVÉ SUR macOS, à la première installation par un humain : la mesure
# employait « df -BG --output=avail », deux options GNU que le df de BSD ne
# connaît pas. La commande échouait, la valeur retombait à zéro, et le pré-vol
# refusait de démarrer un poste qui avait quarante gigaoctets libres. « df -Pk »
# est POSIX : une seule ligne garantie, des blocs de 1 Kio, sur GNU comme sur
# BSD. Le kit annonce macOS et Windows dans INSTALLATION.md : il doit y savoir
# lire un disque.
#
# SECOND PIÈGE, relevé au même essai : le disque QUI COMPTE n'est pas le même
# selon la plateforme. Sous Linux, le magasin d'images et le volume de données
# vivent sur le disque de l'hôte — il lui faut les 10 Go. Sous macOS et Windows,
# ils vivent dans la machine virtuelle podman, et l'hôte ne porte plus que le
# dépôt et l'environnement Python : exiger 10 Go de l'hôte y bloquait un poste
# parfaitement capable, dont la VM avait quarante gigaoctets.
dispo_go="$(df -Pk "$RACINE" 2>/dev/null | awk 'NR==2 {print int($4 / 1048576)}')"
if [ -r /proc/meminfo ]; then
  besoin_hote_go="$MIN_DISQUE_GO"
  ou_hote="le lab y range ses images et ses données"
else
  besoin_hote_go="$MIN_DISQUE_HOTE_GO"
  ou_hote="dépôt et environnement Python seulement ; les données vivent dans la VM"
fi
if [ -n "$dispo_go" ] && [ "$dispo_go" -ge "$besoin_hote_go" ]; then
  ok "${dispo_go} Go libres sur l'hôte (minimum ${besoin_hote_go} Go — ${ou_hote})"
else
  echec "${dispo_go:-0} Go libres sur l'hôte, minimum ${besoin_hote_go} Go."
  faire "Libérez de l'espace, ou déplacez le kit sur un volume plus grand."
fi
# TROISIÈME PIÈGE, relevé à la première installation sur un vrai Windows : sous
# WSL2, « df » mesure le disque VIRTUEL de la distribution, extensible jusqu'à
# 1 To. Le pré-vol y annonçait « 946 Go libres » sur un poste dont le disque C:
# en avait 57. La vraie limite est le disque Windows qui porte ce disque
# virtuel — C: par défaut, où WSL range ses distributions. Plein, il fait
# échouer Elasticsearch en pleine séance, quoi qu'ait dit la mesure précédente.
if grep -qi microsoft /proc/version 2>/dev/null && [ -d /mnt/c ]; then
  win_go="$(df -Pk /mnt/c 2>/dev/null | awk 'NR==2 {print int($4 / 1048576)}')"
  if [ -n "$win_go" ] && [ "$win_go" -ge "$MIN_DISQUE_GO" ]; then
    ok "${win_go} Go libres sur C: (sous WSL2, c'est lui qui borne le disque de la distribution)"
  else
    echec "${win_go:-0} Go libres sur C:, minimum ${MIN_DISQUE_GO} Go : sous WSL2, le disque de la distribution"
    faire "grandit sur C:, et la mesure ci-dessus (son disque virtuel) ne le voit pas."
    faire "Libérez de l'espace sur C:, ou déplacez la distribution : wsl --manage <distribution> --move <dossier>"
  fi
fi
# Hors Linux, on contrôle EN PLUS le disque de la machine podman, qui est celui
# où Elasticsearch écrira réellement.
if [ ! -r /proc/meminfo ]; then
  vm_disque_go="$(podman machine inspect --format '{{.Resources.DiskSize}}' 2>/dev/null \
                  | tr -dc '0-9' | head -c 6)"
  if [ -n "$vm_disque_go" ] && [ "$vm_disque_go" -gt 0 ] 2>/dev/null; then
    if [ "$vm_disque_go" -ge "$MIN_DISQUE_GO" ]; then
      ok "${vm_disque_go} Go sur la machine podman (minimum ${MIN_DISQUE_GO} Go)"
    else
      echec "la machine podman n'a que ${vm_disque_go} Go de disque."
      faire "podman machine stop && podman machine set --disk-size 40 && podman machine start"
    fi
  else
    alerte "Disque de la machine podman non mesurable."
    faire "Assurez-vous qu'elle dispose d'au moins ${MIN_DISQUE_GO} Go."
  fi
fi
# Elasticsearch refuse d'allouer un shard au-delà de ses seuils d'occupation.
# Le lab les exprime en valeur absolue (voir lab/pod.yaml.tmpl) : il suffit donc
# d'avoir l'espace réel, même sur un disque déjà bien rempli en pourcentage.
pct="$(df -Pk "$RACINE" 2>/dev/null | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
if [ -n "$pct" ] && [ "$pct" -ge 90 ]; then
  alerte "Le système de fichiers est occupé à ${pct} %."
  faire "Sans réglage, Elasticsearch bloquerait toute allocation au-delà de 90 %."
  faire "Le lab fixe des seuils absolus (5/3/2 Go) : ce n'est donc pas bloquant ici."
fi

titre "5. Python"
# PIÈGE RELEVÉ À LA PREMIÈRE INSTALLATION PAR UN HUMAIN. « python3 » n'est pas
# le même interpréteur pour tout le monde : sur un Mac avec conda actif, c'est
# un 3.9. L'environnement se créait sans broncher, et l'échec tombait cinq
# commandes plus loin, au chargement des données, sur « cannot import name UTC
# from datetime ». INSTALLATION.md annonçait 3.11 en prérequis ; rien ne le
# vérifiait. Un prérequis non contrôlé n'est pas un prérequis.
py_kit="$RACINE/.venv/bin/python"
[ -x "$py_kit" ] || py_kit="$(command -v python3 || true)"
if [ -z "$py_kit" ]; then
  echec "python3 introuvable."
  faire "Installez Python $MIN_PYTHON ou plus récent."
else
  py_ver="$("$py_kit" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null)"
  if "$py_kit" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    ok "Python $py_ver (minimum $MIN_PYTHON)"
  else
    echec "Python ${py_ver:-inconnu} — le kit exige $MIN_PYTHON ou plus récent."
    faire "Le générateur emploie datetime.UTC, qui n'existe pas avant 3.11."
    faire "macOS : brew install python@3.12"
    faire "        rm -rf .venv && /opt/homebrew/bin/python3.12 -m venv .venv && make venv"
  fi
fi

titre "6. Réseau interne (isolation)"
# Sur un réseau podman « --internal », le trafic entre conteneurs passe par le
# pont. Si br_netfilter renvoie ce trafic vers iptables (bridge-nf-call-iptables
# à 1, ce que fait l'installation de Docker), la règle de blocage posée par
# netavark pour l'isolation coupe AUSSI les échanges internes : le lab devient
# injoignable depuis son propre réseau. Constaté en lab le 21/09/2026.
if [ -r /proc/sys/net/bridge/bridge-nf-call-iptables ]; then
  bnf="$(cat /proc/sys/net/bridge/bridge-nf-call-iptables)"
  if [ "$bnf" = "0" ]; then
    ok "bridge-nf-call-iptables = 0 (réseau podman --internal fonctionnel)"
  else
    alerte "bridge-nf-call-iptables = $bnf : un réseau podman « --internal » bloquerait aussi le trafic interne."
    faire "Sans effet sur un lab lancé sur le réseau podman par défaut."
    faire "Pour exploiter le lab sur un réseau isolé :  sudo sysctl -w net.bridge.bridge-nf-call-iptables=0"
    faire "Cette commande n'est PAS exécutée automatiquement."
  fi
else
  ok "br_netfilter non chargé : rien ne gêne les réseaux podman « --internal »"
fi

titre "7. Ports"
port_occupe() {
  if command -v ss >/dev/null 2>&1; then ss -ltn 2>/dev/null | grep -qE "[:.]$1[[:space:]]"
  elif command -v lsof >/dev/null 2>&1; then lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else return 1; fi
}
for p in "$PORT_ES" "$PORT_KIBANA"; do
  if port_occupe "$p"; then
    # Un lab déjà démarré n'est pas une erreur : « make lab-up » est idempotent.
    if podman pod exists "${KIT_NOM_POD:-kibana-soc-lab}" 2>/dev/null; then
      ok "port $p occupé par le lab lui-même (déjà démarré)"
    else
      echec "port $p déjà occupé par un autre programme."
      faire "Libérez-le, ou choisissez un autre port :  KIT_PORT_ES=19200 KIT_PORT_KIBANA=15601 make lab-up"
    fi
  else
    ok "port $p libre"
  fi
done

titre "8. Images (le lab ne télécharge jamais rien)"
version_stack="$(sed -n 's/^  version:[[:space:]]*"\{0,1\}\([0-9.]*\)"\{0,1\}.*/\1/p' "$RACINE/kit.config.yaml" | head -1)"
if [ -z "$version_stack" ]; then
  echec "Impossible de lire stack.version dans kit.config.yaml."
else
  manquantes=0
  for depot in elasticsearch kibana; do
    if podman image exists "${KIT_DEPOT_IMAGES:-mirror.gcr.io/library}/$depot:$version_stack" 2>/dev/null; then
      ok "image $depot:$version_stack présente localement"
    else
      manquantes=$((manquantes + 1))
      echec "image $depot:$version_stack absente du magasin local."
    fi
  done
  if [ "$manquantes" -gt 0 ]; then
    faire "Livraison hors ligne : podman load -i images/elasticsearch.tar ; podman load -i images/kibana.tar"
    faire "Chaîne de fabrication (en ligne) :  make lab-images"
  fi
fi

titre "Résultat"
if [ "$bloquants" -gt 0 ]; then
  printf '  \033[31m%d blocage(s)\033[0m, %d avertissement(s). Le lab ne peut pas démarrer en l'\''état.\n\n' "$bloquants" "$avertissements"
  exit 1
fi
printf '  \033[32mTout est réuni\033[0m (%d avertissement(s)).\n\n' "$avertissements"
exit 0
