# ORCHESTRATION — déroulé autonome P0 → P8

## Autonomie
- Aucune validation humaine attendue entre les phases. Chaque décision structurante est prise,
  justifiée et consignée dans `docs/JOURNAL.md` : décision · alternatives écartées · raison.
- Arrêt seulement si (a) tous les critères de « Livraison » sont remplis, ou (b) blocage qui exige un
  humain : commande sudo, installation système, ressources insuffisantes, authentification. Afficher
  alors la commande exacte et sa raison, attendre, puis reprendre dès la réponse.
- Chaque phase se termine par l'affichage de la sortie de ses vérifications.

## Orchestration
1. Tu es l'orchestrateur, et ton contexte est la ressource critique. Chaque phase est confiée à un ou
   plusieurs sous-agents d'implémentation (découpe la phase si elle dépasse un contexte), avec un brief
   autonome : objectif, sections de SPEC à relire, fichiers attendus, critères de sortie, pièges de
   CLAUDE.md pertinents. Ils rendent un résumé et la sortie de leurs vérifications.
2. Tu relances ensuite toi-même la vérification de la phase : confiance zéro dans un « c'est fait » non
   prouvé.
3. Recherche documentaire : toujours déléguée à des sous-agents, qui ne rendent que conclusions et URL.
4. Début de phase : relire CLAUDE.md, les sections utiles de `docs/SPEC.md` et `docs/JOURNAL.md`.
   Fin de phase : journal à jour, commit.
5. Les sous-agents `relecteur-expert` et `stagiaire-candide` sont définis dans `.claude/agents/`. S'ils ne
   sont pas disponibles dans la session (fichiers créés en cours de session), lancer un sous-agent
   généraliste avec pour consigne le contenu du fichier correspondant.
6. Deux échecs sur le même problème : changer d'approche et consigner l'impasse.

## Phases et critères de sortie

### P0 — Capacités et plan
- `docs/capacites.md` : chaque capacité de SPEC §4.5 avec version minimale, disponibilité en Basic et
  URL de la documentation officielle de `stack.version`.
- `docs/PLAN.md` : pour P1 → P8, fichiers, cibles make, critères, risques et parades.
- `docs/JOURNAL.md` initialisé.

### P1 — Lab
- `make lab-up` puis `make verif-lab` sortent en 0, sortie affichée : licence basic, santé green, Kibana
  disponible, locale et vue de solution conformes, fonctionnement sur réseau podman `--internal`.
- `make lab-reset` fonctionne ; sa durée est mesurée et consignée.
- Chaque ligne de `docs/capacites.md` est marquée confirmée ou infirmée par un test du lab.

### P2 — Données
- `make data` puis `make verif-donnees` sortent en 0, sortie affichée.
- `data/manifest.json` décrit S1 à S7 ; chaque réponse, recalculée par sa requête DSL, est identique.
- Toute réponse fondée sur un unique count est < 3000. Mapping effectif et `index.mode` affichés et
  conformes à SPEC §5. Deux générations de même graine donnent les mêmes réponses. `make data-epreuve`
  charge le jeu de l'épreuve dans son namespace distinct.

### P3 — Parcours
- D'abord `docs/CHARTE_REDACTION.md` : ton, vocabulaire de la version, anatomie d'un exercice,
  conventions Markdown/YAML. Puis un sous-agent par module, M0 → M5, séquentiellement, tous tenus par
  la charte.
- `make verif-parcours` sort en 0, sortie affichée : chaque requête KQL rejouée dans Discover renvoie le
  nombre attendu, chaque libellé d'interface cité existe dans l'UI du lab, chaque exercice pointe une
  réponse du manifeste, chaque piège de SPEC §6.3 est provoqué dans un exercice.
- `stagiaire-candide` suit M0 → M5 sans blocage ; `relecteur-expert` ne signale aucun écart bloquant.

### P4 — Dashboards corrigés
- « Santé de la collecte » et « Vue IDS » dans `corriges/` (ndjson, plus JSON de l'API Dashboards si
  `stack.version` ≥ 9.5).
- `make verif-corriges` sort en 0, sortie affichée : import dans un Space vierge sans erreur ni
  référence manquante, chaque panneau rendu sans erreur, valeurs affichées égales au manifeste.

### P5 — Design, guide, captures, PDF
- `docs/DESIGN.md` : deux directions visuelles contrastées selon SPEC §7.3, chacune confrontée à la
  liste des clichés ; choix argumenté (ancrage dans le sujet, lisibilité, distinction nette d'avec
  Kibana, accessibilité).
- `make captures`, `make guide`, `make verif-guide` et `make verif-pdf` sortent en 0, sortie affichée.
- Captures du guide examinées en thème clair et sombre, sur ordinateur et mobile ; chaque défaut
  visible corrigé.

### P6 — Formateur et évaluation
- `formateur/` conforme à SPEC §8 et §9. Le script de contrôle montre que la matrice objectifs ×
  exercices × questions couvre 100 % des objectifs. Les PDF passent `make verif-pdf`.

### P7 — Packaging hors ligne
- `make package` produit `dist/` et `SHA256SUMS` ; `make verif-package` sort en 0, sortie affichée.
- `README.md` (démarrage formateur en trois commandes) et README d'installation hors ligne suivis pas
  à pas.

### P8 — Revue finale
- `make verif` complet sort en 0, sortie affichée.
- `stagiaire-candide` suit tout le parcours sans blocage.
- `relecteur-expert` attribue au moins 18/20 selon SPEC §11, aucun critère sous les deux tiers de ses
  points, zéro écart bloquant. Sinon : corriger et relancer, jusqu'à trois cycles ; au-delà, consigner
  l'écart et sa raison.
- `docs/NOTE_DE_CONCEPTION.md` et sa version PDF (4 à 6 pages) : besoin, choix et alternatives écartées,
  architecture, sécurité des données, pédagogie, stratégie de vérification, limites, perspectives.
- `docs/RAPPORT_RECETTE.md` : preuves par phase (commandes, sorties, notes).

## Livraison — message final à l'humain
Tableau des phases (statut, preuve) ; note /20 détaillée ; écarts restants et leur justification ;
commandes de démarrage ; emplacement des livrables ; ce qui reste à faire côté humain (qualification
sur la cible, relecture métier).
