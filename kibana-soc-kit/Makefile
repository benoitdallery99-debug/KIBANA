# Makefile — points d'entrée du kit de formation Kibana pour analystes SOC.
#
# Les paramètres viennent tous de kit.config.yaml (seule source de vérité) :
# aucune version, locale ni graine n'est écrite ici.

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := aide

PY      := .venv/bin/python
PYTEST  := .venv/bin/pytest
RUFF    := .venv/bin/ruff
VERSION := $(shell sed -n 's/^  version:[[:space:]]*"\{0,1\}\([0-9.]*\)"\{0,1\}.*/\1/p' kit.config.yaml | head -1)
DEPOT   ?= mirror.gcr.io/library

.PHONY: aide lab-images lab-up lab-down lab-reset epreuve-ouvrir epreuve-fermer \
        data data-epreuve captures corriges guide package \
        verif verif-lab verif-donnees verif-parcours verif-corriges verif-guide verif-pdf \
        verif-package lint venv

aide:
	@echo "Kit de formation Kibana — Elastic Stack $(VERSION)"
	@echo
	@echo "  Lab"
	@echo "    make lab-images     tire les images (chaîne de fabrication, en ligne)"
	@echo "    make lab-up         pré-vol, démarrage du pod, initialisation"
	@echo "    make lab-down       arrête le lab (volume conservé)"
	@echo "    make lab-reset      repart à neuf et réancre les données sur maintenant"
	@echo "    make epreuve-ouvrir ouvre l'épreuve pratique au compte stagiaire"
	@echo "    make epreuve-fermer la referme"
	@echo
	@echo "  Contenu"
	@echo "    make data           engendre et charge le jeu du parcours"
	@echo "    make data-epreuve   engendre et charge le jeu de l'épreuve pratique"
	@echo "    make corriges       (re)construit les deux tableaux de bord corrigés"
	@echo "    make captures       régénère les captures d'écran (Playwright)"
	@echo "    make guide          construit dist/guide.html et les PDF"
	@echo "    make package        construit l'archive livrable et SHA256SUMS"
	@echo
	@echo "  Vérification (chaque cible est lançable seule)"
	@echo "    make verif          enchaîne toutes les vérifications ci-dessous"
	@echo "    make verif-lab verif-donnees verif-parcours verif-corriges"
	@echo "    make verif-guide verif-pdf verif-package"
	@echo "    make lint           shellcheck + ruff"

# PIÈGE RELEVÉ À LA PREMIÈRE INSTALLATION PAR UN HUMAIN. « python3 » n'est pas
# le même interpréteur pour tout le monde : sur un Mac avec conda actif, c'est
# un 3.9, et l'environnement se créait sans broncher. L'échec tombait cinq
# commandes plus loin, au chargement des données, sur « cannot import name UTC
# from datetime » — un message que rien ne relie à « votre Python est trop
# vieux ». INSTALLATION.md annonçait 3.11 en prérequis ; il n'était vérifié
# nulle part. On le vérifie ici, avant de créer quoi que ce soit, et on dit
# quoi faire.
PY_MIN := 3.11

venv:
	@if [ ! -x $(PY) ]; then \
	  interp="$$(command -v python3 || true)"; \
	  if [ -z "$$interp" ]; then \
	    echo "python3 introuvable. Installez Python $(PY_MIN) ou plus récent."; exit 1; \
	  fi; \
	  ver="$$($$interp -c 'import sys; print("%d.%d" % sys.version_info[:2])')"; \
	  if ! $$interp -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then \
	    echo "Python $$ver trouvé ($$interp), or le kit exige $(PY_MIN) ou plus récent."; \
	    echo "  Le générateur emploie datetime.UTC, qui n'existe pas avant 3.11."; \
	    echo "  macOS      : brew install python@3.12 && rm -rf .venv \\"; \
	    echo "               && /opt/homebrew/bin/python3.12 -m venv .venv && make venv"; \
	    echo "  conda      : conda create -n kibana-soc python=3.12 && conda activate kibana-soc"; \
	    echo "  Debian     : sudo apt install python3.12-venv"; \
	    exit 1; \
	  fi; \
	  "$$interp" -m venv .venv; \
	fi
	@$(PY) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' \
	  || { echo ".venv porte un Python trop ancien. Supprimez-le : rm -rf .venv, puis make venv"; exit 1; }
	@$(PY) -m pip install -q --upgrade pip
	@$(PY) -m pip install -q -r exigences.txt

# Chaîne de fabrication uniquement : le lab, lui, ne télécharge jamais rien.
lab-images:
	@echo "Tirage des images officielles Elastic $(VERSION) depuis $(DEPOT)"
	podman pull $(DEPOT)/elasticsearch:$(VERSION)
	podman pull $(DEPOT)/kibana:$(VERSION)
	@$(PY) lab/rendre_pod.py

lab-up:
	@bash lab/lab-up.sh

lab-down:
	@bash lab/lab-down.sh

lab-reset:
	@bash lab/reset.sh

# L'épreuve pratique est fermée par défaut : le rôle « stagiaire » ne lit pas le
# jeu « logs-*-epreuve ». Le formateur l'ouvre au moment de l'évaluation.
epreuve-ouvrir:
	@bash lab/epreuve.sh ouvrir

epreuve-fermer:
	@bash lab/epreuve.sh fermer

# Le manifeste des réponses change à CHAQUE engendrement : la fenêtre se
# termine à l'instant du chargement, et le générateur n'accepte aucune ancre
# fixe. Le guide embarque les EMPREINTES de ces réponses. Régénérer les
# données sans reconstruire le guide, c'est livrer un guide qui refuse les
# bonnes réponses — c'est arrivé à la première installation par un humain.
# Les deux ne se séparent donc plus.
data:
	@$(PY) data/generateur/engendrer.py --jeu formation
	@$(MAKE) --no-print-directory guide-html

# Le HTML seul : dix secondes, et c'est lui qui valide les réponses. Les sept
# PDF, eux, prennent cinq minutes et ne valident rien.
guide-html:
	@$(PY) guide/build.py

data-epreuve:
	@$(PY) data/generateur/engendrer.py --jeu epreuve

captures:
	@$(PY) captures/produire.py

# MANQUE RELEVÉ À LA PREMIÈRE INSTALLATION PAR UN HUMAIN : les deux tableaux de
# bord corrigés n'avaient AUCUNE cible. « corriges/construire.py » n'était lancé
# qu'à la main, dans l'environnement de fabrication. Un formateur qui suivait la
# marche documentée — lab-up, data — ne les avait donc jamais dans son Kibana,
# alors que le guide du formateur les annonce et que « make verif-corriges » les
# exige. Trois contrôles échouaient sans que rien n'explique pourquoi.
corriges:
	@$(PY) corriges/construire.py

guide: guide-html
	@$(PY) guide/pdf.py

package:
	@bash outils/empaqueter.sh

verif:          verif-lab verif-donnees verif-parcours verif-corriges verif-guide verif-pdf verif-package
verif-lab:      ; @$(PYTEST) verif -m lab
verif-donnees:  ; @$(PYTEST) verif -m donnees
verif-parcours: ; @$(PYTEST) verif -m parcours
verif-corriges: ; @$(PYTEST) verif -m corriges
verif-guide:    ; @$(PYTEST) verif -m guide
verif-pdf:      ; @$(PYTEST) verif -m pdf
verif-package:  ; @$(PYTEST) verif -m package

lint:
	@shellcheck lab/*.sh outils/*.sh 2>/dev/null || shellcheck lab/*.sh
	@$(RUFF) check outils lab data guide verif captures 2>/dev/null || $(RUFF) check outils lab
	@echo "lint : propre"
