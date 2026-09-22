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
| `verif-lab` | 17 | ✅ 17 passés | licence, santé, version, locale, vue de solution, isolation réseau, cloisonnement des quatre Spaces |
| `verif-donnees` | 14 | ✅ 14 passés | volumes, mapping effectif, S1→S7, déterminisme, jeu d'épreuve distinct |
| `verif-parcours` | 20 | ✅ 20 passés | requêtes rejouées, libellés réels, aucune réponse en clair, pièges conformes, réemplois annoncés, corrigé du quiz complet |
| `verif-corriges` | 8 | ✅ 8 passés | import en Space vierge, rendu sans erreur, valeurs conformes |
| `verif-guide` | 14 | ✅ 14 passés | zéro requête réseau, axe-core, empreintes, validation de bout en bout, téléphone, lien d'évitement, entités HTML intactes |
| `verif-pdf` | 10 | ✅ 10 passés | polices embarquées, sommaire paginé, signets, solutions en annexe, aucune réponse dans un document du stagiaire |
| `verif-package` | 8 | ✅ 8 passés | empreintes, complétude, installation sans réseau |
| **Total** | **91** | **✅ zéro échec** | |

Exécution complète après `make lab-reset`, donc sur un lab reconstruit depuis un
volume vide : c'est la seule façon de ne pas confondre « le kit fonctionne » et
« le lab a accumulé de l'état pendant la session ». Deux défauts ne se sont
d'ailleurs montrés que dans ces conditions (voir §P8).

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
17 passed in 43.45s
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
20 passed
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
réponse attendue n'est écrite en clair ; chacun des huit pièges est provoqué par
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
dist/guide.html — 3.08 Mo, 6 modules, 35 exercices, 17 questions de quiz
$ make verif-guide
13 passed
$ make verif-pdf
10 passed
```

Prouve : **zéro requête réseau** à l'ouverture en `file://` ; axe-core injecté
sans violation `serious` ni `critical` ; 3,08 Mo pour une limite de 20 Mo ;
liens internes valides ; texte alternatif sur toutes les images ; empreintes
conformes au manifeste ; **aucune réponse attendue publiée** ; le manifeste
n'est pas embarqué ; et, de bout en bout, **une bonne réponse est acceptée et
une mauvaise refusée**.

Côté PDF : polices embarquées (`pdffonts`), aucune page blanche parasite,
sommaire réellement paginé et pointant dans le document, signets, fiche mémo sur
exactement deux pages, solutions absentes du corps et rassemblées en annexe.

**Sept documents produits**, pagination relevée par `pdfinfo` : `guide.pdf`
(102 pages), `corriges.pdf` (32), `guide-formateur.pdf` (6),
`rapport-recette.pdf` (6), `note-de-conception.pdf` (5),
`quiz-imprimable.pdf` (4), `fiche-memo.pdf` (2).

---

## P6 — Évaluation

```
$ ./.venv/bin/python formateur/matrice.py
Objectifs : 27 · exercices : 35 · questions : 17
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

## P8 — Revue finale

```
$ make lab-reset --oui
Lab remis à neuf.  Données réancrées sur 2026-09-21 22:05.
DUREE_SECONDES=109
$ make verif
17 passed · 14 passed · 20 passed · 8 passed · 14 passed · 10 passed · 8 passed
```

**`make lab-reset` mesuré : 1 min 49 s.** Le critère de sortie P1 exigeait que
cette commande fonctionne et que sa durée soit consignée ; elle n'avait jamais
été lancée, et pour cause — le script qu'elle appelle n'existait pas. Le guide
du formateur le déclarait pourtant non facultatif entre deux sessions.

La suite complète a été rejouée APRÈS cette réinitialisation, donc sur un lab
reconstruit depuis un volume vide. Ce n'est pas un détail de procédure : deux
défauts ne se montrent que dans ces conditions.

- `test_lab_fonctionne_sur_reseau_interne` attendait Elasticsearch en cherchant
  « "status" » dans la réponse. Le corps d'ERREUR en contient un aussi —
  « "status":503 » — que le nœud renvoie tant que `.security-7` n'est pas
  alloué. L'attente sortait donc au premier essai, sur l'erreur. Le contrôle
  passait depuis toujours sans jamais attendre : sur un cluster déjà chaud,
  l'index est alloué et la course ne se produit pas. Signe qui ne trompe pas,
  la suite rendait la main en 36 s au lieu de 44.
- trois des huit réponses ajoutées en P8 comptaient des documents, et dérivaient
  de quelques unités d'une génération à l'autre : les événements sont placés
  relativement à l'instant de génération, avec une pondération sur les heures
  ouvrées. Un stagiaire comptant juste se serait vu répondre « faux ». Remplacées
  par des faits de structure.

### Les deux relectures

`stagiaire-candide` et `relecteur-expert` ont été lancés sur le kit complet. Le
second a rendu **16/20** au premier passage, sous le seuil de 18, avec un écart
bloquant. Les sept écarts ont été corrigés, chacun assorti du contrôle qui
l'aurait vu — c'est ce dernier point qui compte, et qui explique que la suite
soit passée de 78 à 91 contrôles pendant cette revue.

Le bloquant mérite d'être cité, parce qu'il illustre ce que vaut un garde dont
personne ne vérifie la portée. `outils/fuites.py` exemptait les vingt et un
hôtes de la fiche de contexte, au motif qu'une valeur publiée « se perd parmi
ses semblables ». Or le guide n'affiche que les neuf serveurs critiques : les
douze postes de travail étaient exemptés d'un contrôle que CLAUDE.md érige en
définition de « fini », sans figurer nulle part sous les yeux du stagiaire.
Trois réponses de scénario sur sept s'en trouvaient dégardées — et l'une était
déjà partie : `docs/NOTE_DE_CONCEPTION.md` écrivait « le kit n'a jamais besoin
qu'un humain écrive "la réponse est 10.10.13.23" », où cette adresse EST la
réponse attendue de S2.

Second enseignement, trouvé en corrigeant : le garde cherchait ses nombres dans
la totalité du HTML, base64 compris. Une capture régénérée contenait
« …NnSTR+889/gIcJ3… », et « + » comme « / » ne sont pas alphanumériques : la
construction a été refusée sur une réponse qui n'avait fui nulle part. Un garde
qui se joue aux octets d'une image peut aussi bien taire une vraie fuite dans
son bruit. Les charges utiles base64 sont désormais retirées avant la recherche,
et le contrôle a été vérifié dans les deux sens.

### Le parcours suivi par un stagiaire qui ne sait rien

`stagiaire-candide` a suivi les six modules au compte du stagiaire, sans rien
savoir de plus que ce que le guide enseigne, dans l'ordre où il l'enseigne. Il a
buté **neuf fois**, et c'est la relecture qui a le plus rapporté : elle a trouvé
une catégorie de défaut qu'aucun contrôle ne sait formuler — **la consigne
exacte et inapplicable**.

Trois exemples, tous vrais et tous inutilisables tels quels :

- « lisez son type : keyword » — le type EST keyword, et l'interface n'écrit
  jamais ce mot : elle affiche « Mot-clé », en infobulle de l'icône, et rien
  dans le panneau qui s'ouvre au clic ;
- « `PUT /api/dashboards/{id}` » — c'est bien la route, et sans le préfixe
  `kbn:` la console l'envoie à Elasticsearch, qui répond « no handler found » ;
- « une source domine largement » — elle domine de six contre un, et la barre
  latérale affiche 50 % / 50 %, parce qu'avec deux valeurs l'échantillon se
  partage à parts égales.

Deux des neuf venaient des corrections faites pendant cette même phase, et de la
même erreur : avoir choisi une réponse ou un geste sans vérifier que l'écran, à
ce point du parcours, sait le produire. CLAUDE.md le dit pour l'existence — « une
fonctionnalité absente du lab n'existe pas pour le parcours » — ; cela vaut
aussi pour l'ordre.

Enfin, le défaut le plus visible du kit n'avait jamais été vu par personne : la
passe typographique disloquait **1132 entités HTML**, si bien que le sommaire
annonçait « Pourquoi l' ;écran est-il vide ». Le contrôle de typographie
passait, et il avait raison : il examine le texte extrait, où l'entité est déjà
résolue. Il ne regardait pas là.

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
| E8 | SPEC §9 demande un quiz de 15 questions ; le kit en livre 17 | Mineur | Assumé : Q16 et Q17 couvrent les deux pièges d'interface de SPEC §6.3, que rien n'évaluait. Écart dans le sens du mieux, mais écart tout de même — d'où cette ligne |
| E9 | Le dépôt distant refuse le `push` : 403, l'application GitHub n'a pas le droit `Contents: write` sur `YamTeam9/picturegallery` | Bloquant pour la livraison, nul pour le kit | Non résolu, hors de portée : relève d'un administrateur de l'organisation. Le travail est remis sous forme de bundle git complet |

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
