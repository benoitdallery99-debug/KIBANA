# PLAN — P1 à P8 : fichiers, cibles, critères, risques

Établi en P0, tenu à jour à chaque phase. L'état réel fait foi dans `docs/JOURNAL.md` ; ce document
dit ce qui est prévu, le journal dit ce qui s'est passé et pourquoi.

Rappel des paramètres (`kit.config.yaml`) : Elastic Stack **9.5.3**, licence **Basic**, locale
**fr-FR**, vue de solution **classic**, graine **20260921**, fenêtre **7 jours**.

| Phase | État |
|---|---|
| P0 Capacités et plan | **terminée** — `docs/capacites.md` (90 lignes de capacités, 19 confirmées en lab), `docs/capacites-lab.json`, `docs/pieges-lab.json`, ce plan |
| P1 Lab | **terminée** — `make verif-lab` : 13 passés |
| P2 Données | **terminée** — `make verif-donnees` : 14 passés |
| P3 Parcours | à faire |
| P4 Tableaux de bord corrigés | **terminée** (avant P3, décision D9) — `make verif-corriges` : 8 passés |
| P5 Design, guide, captures, PDF | à faire |
| P6 Formateur et évaluation | à faire |
| P7 Empaquetage hors ligne | à faire |
| P8 Revue finale | à faire |

---

## P1 — Lab · TERMINÉE

**Fichiers** `lab/pod.yaml.tmpl`, `lab/rendre_pod.py`, `lab/preflight.sh`, `lab/lab-up.sh`,
`lab/lab-down.sh`, `lab/reset.sh`, `lab/init/init.py`, `lab/images.yaml`, `outils/conf.py`, `Makefile`.
**Cibles** `make lab-up`, `lab-down`, `lab-reset`, `lab-images`, `verif-lab`.
**Critères** licence `basic`, santé `green`, Kibana disponible, locale et vue conformes, réseau podman
`--internal` fonctionnel et sans sortie possible.
**Risques et parades** — réalisés, voir D6 et D7 du journal : seuils disque en pourcentage (parade :
seuils absolus) ; `bridge-nf-call-iptables` à 1 qui casse les réseaux isolés (parade : contrôle au
pré-vol, commande `sudo` affichée et jamais exécutée).

## P2 — Données · TERMINÉE

**Fichiers** `data/generateur/{contexte,gabarits,temps,evenements,scenarios,engendrer}.py`,
`data/manifest.json`, `data/manifest-epreuve.json`.
**Cibles** `make data`, `make data-epreuve`, `make verif-donnees`.
**Critères** 384 592 documents, mapping effectif et `index.mode` conformes, S1 à S7 présents, chaque
réponse recalculée par sa requête DSL, déterminisme, jeu d'épreuve distinct.
**Risque résiduel** aucune réponse ne dépend d'un `unique count` ≥ 3000 ; contrôlé par un test dédié.

## P3 — Parcours · À FAIRE

**Fichiers** `docs/CHARTE_REDACTION.md` d'abord, puis `parcours/M0.md` … `parcours/M5.md`
(Markdown + frontmatter YAML : objectifs, durée, exercices, réponses par renvoi au manifeste).
**Cible** `make verif-parcours`.
**Critères de sortie**
- chaque requête KQL du parcours, tapée dans Discover par Playwright, renvoie le nombre attendu ;
- chaque libellé d'interface cité existe dans l'UI fr-FR du lab ;
- chaque exercice renvoie à une réponse du manifeste, jamais à une valeur écrite à la main ;
- chacun des pièges de SPEC §6.3 est provoqué dans un exercice, avec le comportement RÉEL relevé dans
  `docs/pieges-lab.json` ;
- `stagiaire-candide` va de M0 à M5 sans blocage ; `relecteur-expert` ne signale aucun écart bloquant.

**Ce que `docs/capacites.md` impose au parcours** (à ne pas redécouvrir)
- Drilldown **URL** : hors Basic (Gold). M3 n'enseigne que dashboard → dashboard et le passage vers
  Discover. Encadré « Hors licence Basic ».
- **Rapports PDF/PNG** : hors Basic. Encadré, car l'absence surprend. L'export CSV, lui, existe.
- **Planification d'exports récurrents** : hors Basic, y compris en CSV, et la documentation ne le dit
  nulle part. Second encadré, en M5.
- **Connecteurs d'alerte** : `.index` et `.server-log` seulement (2 sur 73, relevé sur le lab). M5 s'y
  tient.
- **API Dashboards** : servie en Basic, routes `PUT /api/dashboards/{id}` et `POST /api/dashboards`.
  Enseignée en M5.
- **Terminologie fr-FR** : « Session Discover », « Tableaux de bord », « Section pliable ». Les libellés
  cités viennent du relevé, jamais d'une traduction faite de tête.

**Risques et parades**
| Risque | Parade |
|---|---|
| Un exercice dont la réponse se devine sans le faire | Chaque exercice renvoie à une réponse du manifeste, dont la valeur dépend de la graine ; un contrôle refuse tout exercice sans renvoi |
| Un libellé d'UI inventé ou traduit de tête | Contrôle Playwright : le libellé doit exister dans l'UI fr-FR du lab |
| Une requête du guide qui ne donne pas le nombre annoncé | Toutes les requêtes sont rejouées dans Discover |
| Un piège décrit autrement qu'il ne se comporte | `docs/pieges-lab.json` fait foi (voir écart E6) |

## P4 — Tableaux de bord corrigés · TERMINÉE

**Fichiers** `corriges/construire.py`, `corriges/kit-soc-sante-collecte.json`,
`corriges/kit-soc-vue-ids.json`, `corriges/tableaux-de-bord.ndjson`, `verif/e2e/kibana.py`.
**Cible** `make verif-corriges`.
**Contraintes relevées** l'API refuse les panneaux `map` et `alerts_table`, ainsi qu'un `filter` au
niveau du panneau, et toute référence à une data view par identifiant : les corrigés n'en emploient
aucun.

## P5 — Design, guide, captures, PDF · À FAIRE

**Fichiers** `docs/DESIGN.md` (deux directions contrastées, confrontées aux clichés de SPEC §7.3, choix
argumenté) ; `guide/build.py`, gabarits Jinja2, styles, polices OFL, JS vanilla ; `captures/produire.py`.
**Cibles** `make captures`, `make guide`, `make verif-guide`, `make verif-pdf`.
**Critères** `dist/guide.html` en un seul fichier, zéro requête réseau, ≤ 20 Mo, axe-core sans violation
serious ou critical, liens internes valides, textes alternatifs partout, empreintes égales au manifeste ;
PDF aux polices embarquées, sommaire paginé, signets, sans page blanche parasite.
**Risques et parades**
| Risque | Parade |
|---|---|
| Une ressource externe oubliée dans le HTML | Contrôle Playwright : toute requête réseau sortante fait échouer `verif-guide` |
| 20 Mo dépassés par les captures | WebP, `deviceScaleFactor` 2, contrôle de taille dans la cible |
| Validation des réponses qui révèle la réponse | Le guide n'embarque que des empreintes SHA-256 ; contrôle que le manifeste n'est pas embarqué |
| Polices OFL à noms réservés | Embarquées telles que distribuées, sans sous-ensemble ni conversion |

## P6 — Formateur et évaluation · À FAIRE

**Fichiers** `formateur/guide-formateur.md`, `formateur/quiz.md` (15 questions),
`formateur/epreuve-pratique.md`, `formateur/evaluation-a-chaud.md`, `formateur/matrice.py`.
**Critères** la matrice objectifs × exercices × questions couvre 100 % des objectifs, prouvé par script ;
l'épreuve n'embarque aucune réponse, pas même une empreinte ; les PDF passent `make verif-pdf`.

## P7 — Empaquetage hors ligne · À FAIRE

**Fichiers** `outils/empaqueter.sh`, `README.md`, `dist/` (engendré), `SHA256SUMS`.
**Cible** `make package`, `make verif-package`.
**Critères** installation depuis l'archive dans un répertoire vierge, sur réseau `--internal`, sans
aucun téléchargement ; M0 rejoué par Playwright ; empreintes valides.
**Risque** les images pèsent 3,5 Go : `podman save` compressé, et l'archive documente la taille attendue.

## P8 — Revue finale · À FAIRE

**Fichiers** `docs/NOTE_DE_CONCEPTION.md` (+ PDF, 4 à 6 pages), `docs/RAPPORT_RECETTE.md`.
**Critères** `make verif` complet en 0 ; `stagiaire-candide` sur tout le parcours ; `relecteur-expert`
au moins 18/20 selon SPEC §11, aucun critère sous les deux tiers, zéro écart bloquant ; au plus trois
cycles de correction, au-delà l'écart est consigné et justifié.
