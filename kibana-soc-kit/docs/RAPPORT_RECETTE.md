# Rapport de recette

Kit de formation Kibana pour analystes SOC. Elastic Stack **9.5.3**, licence
**Basic**, interface **fr-FR**, vue de solution **classic**.

Ce document rassemble les preuves, phase par phase : la commande lancée, ce
qu'elle a répondu, et ce que cela établit. Un contrôle non exécuté y figure
comme **non exécuté**, avec sa raison — jamais comme réussi.

---

## Vue d'ensemble

| Suite | Contrôles | Résultat | Ce qui est prouvé |
|---|---|---|---|
| `verif-lab` | 13 | à rejouer | licence, santé, version, locale, vue de solution, isolation réseau |
| `verif-donnees` | 14 | à rejouer | volumes, mapping effectif, S1→S7, déterminisme, jeu d'épreuve distinct |
| `verif-parcours` | 16 | à rejouer | requêtes rejouées, libellés réels, aucune réponse en clair, pièges conformes |
| `verif-corriges` | 8 | à rejouer | import en Space vierge, rendu sans erreur, valeurs conformes |
| `verif-guide` | 11 | à rejouer | zéro requête réseau, axe-core, empreintes, validation de bout en bout |
| `verif-pdf` | 8 | à rejouer | polices embarquées, sommaire paginé, signets, solutions en annexe |
| `verif-package` | 8 | à rejouer | empreintes, complétude, installation sans réseau |
| **Total** | **78** | | |

> **État de ce rapport.** Les relectures `stagiaire-candide` et
> `relecteur-expert` de la phase P8 ont ouvert des écarts bloquants ; les
> corrections sont en cours et touchent le lab, le parcours, les corrigés et le
> guide. Les chiffres ci-dessus sont ceux des suites telles qu'elles existent
> aujourd'hui dans `verif/`, mais **leur dernier passage vert est antérieur à
> ces corrections** : ils sont donc marqués « à rejouer », et non « passés ».
> Les sorties reproduites plus bas dans ce document sont celles de cette
> exécution antérieure — elles sont conservées comme trace, pas comme preuve de
> l'état actuel. Ce rapport est régénéré en fin de P8, une fois `make verif`
> relancé en entier.

Qualité du code : `shellcheck` sur tous les scripts, `ruff` sur tout le Python —
propres, sans exception ni dérogation.

---

## P0 — Capacités

**Méthode.** 13 sous-agents ont dépouillé la documentation Elastic officielle,
lue dans son dépôt source (`github.com/elastic/docs-content`), `www.elastic.co`
étant bloqué par la politique d'egress du poste de fabrication. 270 constats,
chacun avec son badge `applies_to`, son fichier source et son URL canonique.
Puis `lab/sonder_capacites.py` et `lab/sonder_pieges.py` ont interrogé le lab.

**Résultat.** `docs/capacites.md` — 90 capacités en 13 familles.

| Colonne « confirmé en lab » | Nombre |
|---|---|
| ✔ confirmé | 19 |
| ✘ infirmé | 7 |
| — non sondé | 64 |

Les 64 non sondées le restent explicitement, avec le test qui les trancherait.
Aucune n'étaye une affirmation du parcours.

**Constats déterminants, relevés sur le lab :**

```
Licence : basic (active)
API Dashboards servie   : True (création HTTP 201)
ES|QL disponible        : True
Connecteurs utilisables : 2 / 73 → ['.index', '.server-log']
Types de règles         : 41 / 47 utilisables
```

Les deux connecteurs disponibles confirment exactement l'attendu de SPEC §4.5.

---

## P1 — Lab

```
$ make verif-lab
13 passed in 57.28s
```

Prouve : licence `basic`, santé `green`, Elasticsearch et Kibana en 9.5.3,
locale fr-FR servie (60 705 clés), vue de solution `classic`, data views à
identifiant fixe, rôles et comptes, connexion de Kibana par `kibana_system`,
images épinglées par digest avec `imagePullPolicy: Never`, cartes et télémétrie
coupées, **fonctionnement sur réseau podman `--internal`** et **impossibilité
d'en sortir**.

Le contrôle d'isolation porte un témoin : sur le réseau interne la connexion
sortante échoue faute de route (`rc=7`), alors que sur le réseau par défaut la
même requête établit bien une connexion. Sans ce témoin, le contrôle ne
prouverait rien.

**Durées mesurées.** Elasticsearch prêt en 36 s ; `make lab-up` complet en moins
de 2 min sur 4 cœurs. La cible « moins de cinq minutes » de SPEC §4.4 est tenue.

---

## P2 — Données

```
$ make data
Total : 386 496 documents
$ make verif-donnees
14 passed in 20.72s
```

Six sources, fenêtre glissante de 7 jours, rythme ouvré vérifié (≈ 4 400 à
4 800 événements par heure en pic contre 105 à 3 h ; samedi à 16 % et dimanche à
10 % d'un jour ouvré).

Prouve notamment :
- chaque réponse du manifeste **recalculée par sa propre requête DSL** donne la
  même valeur ;
- le mapping **effectif** est conforme (`ip` pour les adresses, `keyword` pour
  les identifiants, `text` pour `message`) et `index.mode` vaut `standard` ;
- deux générations de même graine donnent les mêmes réponses ;
- toutes les adresses indexées sont dans les plages réservées (RFC 5737,
  RFC 1918) et tous les domaines en `.test` ou `.example` — contrôlé sur les
  **valeurs effectivement indexées**, pas sur l'intention du générateur ;
- aucune réponse ne repose sur un décompte distinct supérieur à 3 000 ;
- le jeu `epreuve` a les mêmes structures et des réponses différentes.

---

## P3 — Parcours

```
$ make verif-parcours
16 passed
```

Six modules, **347 minutes**, **35 exercices**, **27 objectifs**.

| Module | Durée | Exercices | Guidage |
|---|---|---|---|
| M0 Prise en main | 30 min | 3 | démonstration → guidé → semi-guidé |
| M1 Rechercher avec Discover | 75 min | 6 | démonstration → … → autonome |
| M2 Visualiser avec Lens | 60 min | 6 | démonstration → … → autonome |
| M3 Construire un tableau de bord | 60 min | 6 | démonstration → … → autonome |
| M4 Capstone SOC | 90 min | 10 | **autonome** de bout en bout |
| M5 Industrialiser | 30 min | 4 | démonstration → … → autonome |

Prouve : chaque requête KQL **tapée dans Discover** renvoie ce qui est annoncé ;
chaque libellé d'interface cité **existe** dans l'interface fr-FR du lab ; aucune
réponse attendue n'est écrite en clair ; chacun des six pièges est provoqué par
un exercice et **décrit tel qu'il se comporte** ; le guidage est dégressif ;
chaque objectif est évalué par au moins un exercice.

---

## P4 — Tableaux de bord corrigés

```
$ make verif-corriges
8 passed in 58.98s
```

« Santé de la collecte » (5 panneaux) et « Vue IDS » (7 panneaux), définis en
code par l'API Dashboards puis exportés en ndjson.

Prouve : import dans un Space **vierge** sans erreur ni référence manquante ;
panneaux non vides après import ; **les 12 panneaux se rendent sans erreur**
(Playwright) ; la valeur affichée égale le décompte d'Elasticsearch sur la même
fenêtre ; et le corrigé **révèle effectivement le scénario S6** — l'indicateur
« sources actives sur la dernière heure » passe sous six, et la source muette
arrive en tête du tableau du dernier événement vu.

---

## P5 — Guide, captures, PDF

```
$ make guide
dist/guide.html — 1.99 Mo, 6 modules, 35 exercices, 15 questions de quiz
$ make verif-guide
10 passed
$ make verif-pdf
7 passed
```

Exécution antérieure aux corrections de P8 : `verif-guide` comptait alors 10
contrôles et `verif-pdf` 7 ; ils en comptent aujourd'hui 11 et 8, et doivent
être rejoués.

Prouve : **zéro requête réseau** à l'ouverture en `file://` ; axe-core injecté
sans violation `serious` ni `critical` ; 1,99 Mo pour une limite de 20 Mo ;
liens internes valides ; texte alternatif sur toutes les images ; empreintes
conformes au manifeste ; **aucune réponse attendue publiée** ; le manifeste
n'est pas embarqué ; et, de bout en bout, **une bonne réponse est acceptée et
une mauvaise refusée**.

Côté PDF : polices embarquées (`pdffonts`), aucune page blanche parasite,
sommaire réellement paginé et pointant dans le document, signets, fiche mémo sur
exactement deux pages, solutions absentes du corps et rassemblées en annexe.

**Sept documents produits**, pagination relevée par `pdfinfo` : `guide.pdf`
(96 pages), `corriges.pdf` (30), `rapport-recette.pdf` (6),
`guide-formateur.pdf` (5), `note-de-conception.pdf` (4),
`quiz-imprimable.pdf` (3), `fiche-memo.pdf` (2).

---

## P6 — Évaluation

```
$ ./.venv/bin/python formateur/matrice.py
Objectifs : 27 · exercices : 35 · questions : 15
Couverture complète (exercice ET question) : 27/27 soit 100 %
code de sortie: 0
```

Le script sort en 1 si un seul objectif reste sans exercice ou sans question :
la couverture est donc prouvée, pas affirmée.

---

## P7 — Archive hors ligne

```
$ make verif-package
8 passed in 48.83s
```

Prouve : empreinte de l'archive conforme ; **toutes** les lignes de `SHA256SUMS`
valides ; archive complète (images de conteneurs, wheels, guide, PDF, corrigés,
sources, documentation) ; le manifeste de l'épreuve — qui porte ses réponses —
**n'est pas livré** au stagiaire ; aucun secret ne voyage ; le pré-vol s'exécute
depuis l'archive ; le guide livré s'ouvre hors ligne sans aucune requête.

L'installation hors ligne est éprouvée en pointant **toutes les variables de
proxy vers un port mort** : si pip tentait d'atteindre PyPI, il échouerait au
lieu de réussir en silence.

---

## Défauts trouvés par la vérification, et corrigés

Aucun n'était visible à la lecture. Tous ont été corrigés **à la cause**, jamais
en assouplissant un critère.

| # | Défaut | Comment il est apparu |
|---|---|---|
| 1 | Un réglage Elasticsearch inventé (`telemetry.enabled`) empêchait le nœud de démarrer | Premier `lab-up` |
| 2 | Seuils d'occupation disque en pourcentage : cluster `red` avec 24,9 Go libres | Santé du cluster |
| 3 | Une suite de vérification **détruisait le lab qu'elle vérifiait** (`network rm -f`) | Le lab a disparu |
| 4 | Le domaine de la balise S3 n'était pas distinguable des domaines internes | Recalcul par requête |
| 5 | Le leurre S7 ne dominait pas le décompte qu'il devait dominer | Recalcul par requête |
| 6 | Deux réponses identiques entre parcours et épreuve | Contrôle de distinction |
| 7 | Un indicateur mesuré sur 7 j restait au vert malgré une source muette | Rendu du tableau de bord |
| 8 | Sélecteurs d'interface périmés — ils n'échouent pas, ils ne trouvent rien | Avertissement des captures |
| 9 | La jauge de progression affichait un caractère illisible (glyphe absent de la police) | Capture d'écran |
| 10 | Les tableaux débordaient de l'écran sur téléphone | Capture à 390 px |
| 11 | Les contrôles de S6 mesurés « depuis maintenant » : verts après `make data`, **rouges une heure plus tard** | Relance à froid |

---

## Corrections apportées à des prémisses de la spécification

Deux affirmations de `docs/SPEC.md` se sont révélées fausses **en 9.5.3**. La
SPEC n'a pas été modifiée ; l'écart est consigné et c'est le comportement
constaté qui est enseigné, comme SPEC §6.3 l'exige elle-même.

1. **`destination.port : [1025 TO *]` ne produit pas un « échec silencieux ».**
   Kibana affiche « Impossible d'extraire les résultats de recherche ». Le piège
   réellement muet est `_exists_ : champ`, qui renvoie zéro sans rien dire.
2. **Les drilldowns URL exigent une licence Gold.** La documentation ne le dit
   nulle part ; c'est le code de la version qui l'établit. M3 est recomposé et
   porte un encadré « Hors licence Basic ».

---

## Écarts ouverts

| ID | Écart | Gravité | Statut |
|---|---|---|---|
| E1 | `elastic.co` et `docker.elastic.co` bloqués par la politique d'egress du poste de fabrication | Majeur, chaîne de fabrication seulement | Contourné : images par miroir à digest vérifié identique, documentation lue dans son dépôt source. Sans effet sur le livrable, hors ligne par construction |
| E4 | La version 9.5.4, dernière stable annoncée, n'est pas disponible sur le miroir | Mineur | Accepté : kit construit et vérifié en 9.5.3, la montée de version tient dans une ligne de `kit.config.yaml` |
| E6 | Deux prémisses de la SPEC corrigées (voir ci-dessus) | Mineur | Résolu, SPEC non modifiée, comportement réel enseigné |
| E7 | 64 capacités sur 90 non sondées dans le lab | Mineur | Assumé et signalé : aucune n'étaye une affirmation du parcours |

---

## Ce qui reste à faire, côté humain

1. **Qualifier le kit sur la plateforme cible.** Il a été fabriqué et vérifié sur
   une seule machine. Sur la cible, relancer `make verif` et reprendre les
   lignes « non sondé » de `docs/capacites.md` qui concernent votre usage.
2. **Relire le contenu métier.** Le contexte fictif — plan d'adressage, serveurs
   critiques, comptes de service — gagnerait à être rapproché de votre
   topologie réelle, sans y introduire aucune donnée réelle.
3. **Faire une session à blanc** avec deux ou trois analystes, et exploiter la
   fiche d'évaluation à chaud : c'est elle qui doit piloter la première
   correction du parcours.
