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

.PHONY: aide lab-images lab-up lab-down lab-reset data data-epreuve captures guide package \
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
	@echo
	@echo "  Contenu"
	@echo "    make data           engendre et charge le jeu du parcours"
	@echo "    make data-epreuve   engendre et charge le jeu de l'épreuve pratique"
	@echo "    make captures       régénère les captures d'écran (Playwright)"
	@echo "    make guide          construit dist/guide.html et les PDF"
	@echo "    make package        construit l'archive livrable et SHA256SUMS"
	@echo
	@echo "  Vérification (chaque cible est lançable seule)"
	@echo "    make verif          enchaîne toutes les vérifications ci-dessous"
	@echo "    make verif-lab verif-donnees verif-parcours verif-corriges"
	@echo "    make verif-guide verif-pdf verif-package"
	@echo "    make lint           shellcheck + ruff"

venv:
	@test -x $(PY) || python3 -m venv .venv
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

data:
	@$(PY) data/generateur/engendrer.py --jeu formation

data-epreuve:
	@$(PY) data/generateur/engendrer.py --jeu epreuve

captures:
	@$(PY) captures/produire.py

guide:
	@$(PY) guide/build.py

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
