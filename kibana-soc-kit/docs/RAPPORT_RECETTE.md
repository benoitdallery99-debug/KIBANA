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
| `verif-lab` | 20 | ✅ 20 passés | licence, santé, version, locale, vue de solution, isolation réseau, cloisonnement des quatre Spaces, fuseau d'affichage posé dans chacun, pré-vol portable hors GNU, tout prérequis annoncé est contrôlé |
| `verif-donnees` | 14 | ✅ 14 passés | volumes, mapping effectif, S1→S7, déterminisme, jeu d'épreuve distinct |
| `verif-parcours` | 33 | ✅ 33 passés | requêtes rejouées, libellés réels, aucune réponse en clair, pièges conformes, réemplois annoncés, corrigé du quiz complet, positions du quiz réparties, aucune empreinte validée deux fois, tableau des types adossé au lab, requêtes ES|QL du corps rejouées, aucune requête écrite en ligne, contraste de cardinalité réellement présent, un seul mot pour la fenêtre de temps, déroulé minuté recalculé, aucun évaluateur unique proposé au sacrifice, versions citées liées à la configuration, indices à deux niveaux |
| `verif-corriges` | 9 | ✅ 9 passés | import en Space vierge, rendu sans erreur, valeurs conformes, décomptes de panneaux publiés recomptés |
| `verif-guide` | 25 | ✅ 25 passés | zéro requête réseau, axe-core, empreintes, validation de bout en bout, téléphone, lien d'évitement, entités HTML intactes, toute capture visant un Space à réponses est épinglée sur une plage antérieure au jeu — donc sur des panneaux vides —, sommaire atteignable après défilement, recherche qui surligne, position courante au niveau de l'exercice, capture agrandie à sa taille réelle, filet à 3:1 sur les quatre fonds, contrat de docs/DESIGN.md relu |
| `verif-pdf` | 10 | ✅ 10 passés | polices embarquées, sommaire paginé, signets, solutions en annexe, aucune réponse dans un document du stagiaire |
| `verif-package` | 10 | ✅ 10 passés | empreintes, complétude, installation sans réseau, chiffres de ce rapport recomptés, toute dépendance importée est déclarée |
| **Total** | **121** | **✅ zéro échec** | |

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
20 passed in 49.00s
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
14 passed in 18.03s
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
33 passed in 127.97s
```

Six modules, **407 minutes**, **35 exercices**, **27 objectifs**. La durée d'un
module couvre tout ce qu'il demande : ses exercices, la lecture de son corps et
son rappel actif. Elle ne les couvrait pas avant le troisième tour de relecture,
et valait exactement la somme des exercices dans quatre modules sur six.

| Module | Durée | Exercices | Guidage |
|---|---|---|---|
| M0 Prise en main | 37 min | 3 | démonstration → guidé → semi-guidé |
| M1 Rechercher avec Discover | 87 min | 6 | démonstration → … → autonome |
| M2 Visualiser avec Lens | 71 min | 6 | démonstration → … → autonome |
| M3 Construire un tableau de bord | 70 min | 6 | démonstration → … → autonome |
| M4 Capstone SOC | 98 min | 10 | **autonome** de bout en bout |
| M5 Industrialiser | 44 min | 4 | démonstration → … → autonome |

Prouve : chaque requête KQL **tapée dans Discover** renvoie ce qui est annoncé ;
chaque libellé d'interface cité **existe** dans l'interface fr-FR du lab ; aucune
réponse attendue n'est écrite en clair ; chacun des huit pièges est provoqué par
un exercice et **décrit tel qu'il se comporte** ; le guidage est dégressif ;
chaque objectif est évalué par au moins un exercice.

---

## P4 — Tableaux de bord corrigés

```
$ make verif-corriges
9 passed in 51.52s
```

« Santé de la collecte » (5 panneaux) et « Vue IDS » (8 panneaux), définis en
code par l'API Dashboards puis exportés en ndjson.

Prouve : import dans un Space **vierge** sans erreur ni référence manquante ;
panneaux non vides après import ; **les 13 panneaux se rendent sans erreur**
(Playwright) ; la valeur affichée égale le décompte d'Elasticsearch sur la même
fenêtre ; et le corrigé **révèle effectivement le scénario S6** — l'indicateur
« sources actives sur la dernière heure » passe sous six, et la source muette
arrive en tête du tableau du dernier événement vu.

---

## P5 — Guide, captures, PDF

```
$ make guide
dist/guide.html — 2.88 Mo, 6 modules, 35 exercices, 17 questions de quiz
$ make verif-guide
25 passed in 28.02s
$ make verif-pdf
10 passed in 281.15s
```

Prouve : **zéro requête réseau** à l'ouverture en `file://` ; axe-core injecté
sans violation `serious` ni `critical` ; 2,88 Mo pour une limite de 20 Mo ;
liens internes valides ; texte alternatif sur toutes les images ; empreintes
conformes au manifeste ; **aucune réponse attendue publiée** ; le manifeste
n'est pas embarqué ; et, de bout en bout, **une bonne réponse est acceptée et
une mauvaise refusée**.

Côté PDF : polices embarquées (`pdffonts`), aucune page blanche parasite,
sommaire réellement paginé et pointant dans le document, signets, fiche mémo sur
exactement deux pages, solutions absentes du corps et rassemblées en annexe.

**Sept documents produits**, pagination relevée par `pdfinfo` : `guide.pdf`
(117 pages), `corriges.pdf` (46), `rapport-recette.pdf` (11),
`guide-formateur.pdf` (7), `note-de-conception.pdf` (5),
`quiz-imprimable.pdf` (4), `fiche-memo.pdf` (2). Le guide et les corrigés ont
gagné des pages au troisième tour : chaque capture y occupe désormais une page
A4 paysage qui lui est propre, faute de quoi elle s'imprimait à 153 mm de large
et le texte de Kibana y tombait sous 4 points.

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
10 passed in 145.98s
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
20 passed · 14 passed · 33 passed · 9 passed · 25 passed · 10 passed · 10 passed
```

Cette transcription est celle du PREMIER tour de revue, et elle totalise 91.
Les deux tours suivants ont ajouté cinq contrôles ; la voici rejouée en entier
après les corrections du troisième, sur les données et les captures
régénérées — c'est elle qui fait foi, et c'est elle que le tableau de synthèse
recopie :

```
$ make data && make data-epreuve && .venv/bin/python corriges/construire.py
  [OK] Santé de la collecte       5 panneaux (HTTP 200)
  [OK] Vue IDS                    8 panneaux (HTTP 200)
$ make captures
8 capture(s) dans captures/images
$ make guide
dist/guide.html — 2.88 Mo, 6 modules, 35 exercices, 17 questions de quiz
$ make verif
20 passed in 49.00s       (verif-lab)
14 passed in 18.03s       (verif-donnees)
33 passed in 127.97s      (verif-parcours)
9 passed in 51.52s        (verif-corriges)
25 passed in 28.02s       (verif-guide)
10 passed in 281.15s      (verif-pdf)
10 passed in 145.98s      (verif-package)
$ echo $?
0
$ make package && make verif-package
Archive prête : dist/kit-formation-kibana-9.5.3-20260922.tar.gz (1409 Mo)
10 passed in 45.01s
```

L'empreinte de l'archive n'est pas recopiée ici, et c'est volontaire : ce
document EST dans l'archive, donc toute empreinte qu'il citerait serait celle
d'une archive antérieure à lui-même. Elle se lit dans
`dist/kit-formation-kibana-9.5.3-20260922.tar.gz.sha256`, écrit par la même
commande, et `SHA256SUMS` couvre chaque fichier du paquet.

Soit **99 contrôles, zéro échec**. Le tableau de synthèse annonçait 94 « zéro
échec » alors que la seule transcription du document en montrait 91 : c'était
le second écart bloquant du troisième tour, et la récidive exacte de la faute
dont le kit avait tiré sa règle plus haut dans cette même phase. Un chiffre
recompté dans les fichiers de test n'est pas une exécution.

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

### Les relectures

`stagiaire-candide` et `relecteur-expert` ont été lancés sur le kit complet.
Le premier a buté **neuf fois** ; le second a rendu **16/20** au premier
passage, sous le seuil de 18, avec un écart bloquant ; **16,5/20** au deuxième,
toujours sous le seuil, avec un autre bloquant ; **11,8/20** au troisième, mené
autrement et bien plus loin — neuf relecteurs et autant de contre-experts. Les
seize écarts du premier tour — sept de l'expert, neuf du candide — ont été
corrigés, chacun assorti du contrôle qui l'aurait vu ; c'est ce dernier point
qui compte, et qui explique que la suite soit passée de 78 à 91 contrôles
pendant cette revue, puis à 94, puis à **99**.

Le bloquant du premier tour mérite d'être cité, parce qu'il illustre ce que
vaut un garde dont personne ne vérifie la portée. `outils/fuites.py` exemptait
les vingt et un hôtes de la fiche de contexte, au motif qu'une valeur publiée
« se perd parmi ses semblables ». Or le guide n'affiche que les neuf serveurs critiques : les
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

### Le second passage de l'expert, et le bloquant qu'il a trouvé

Le kit corrigé est repassé devant `relecteur-expert`, qui a rendu **16,5/20** —
au-dessus du premier tour, toujours sous le seuil de 18, et avec un nouvel écart
bloquant. Il mérite d'être cité entier, parce qu'il montre la limite exacte des
gardes écrits jusque-là.

Les captures **M3-C1** et **M4-C1** étaient prises dans le Space `corriges`, sur
les tableaux de bord du corrigé, à leur plage de temps enregistrée. Les
indicateurs y affichaient donc les nombres attendus, et les titres de panneaux
sont, mot pour mot, les questions posées aux exercices. Douze exercices se
résolvaient en regardant le guide, sans ouvrir Kibana. `outils/fuites.py` lit du
texte : une image ne passe sous aucun de ses filtres, et il n'a rien signalé —
il n'avait rien à signaler.

Les deux captures restent dans le guide, parce que la STRUCTURE d'un tableau de
bord — la place de l'indicateur, l'ordre des panneaux, la formulation des titres
en questions — s'enseigne mal sans image. Elles sont désormais prises sur une
plage réglée dix ans en arrière : les panneaux sont vides, et c'est dit dans la
légende comme dans le texte alternatif. Le contrôle qui l'aurait vu existe :
`test_aucune_capture_du_guide_ne_montre_les_donnees_d_un_space_a_reponses`
refuse toute capture visant `corriges` ou `epreuve` dont le chemin n'épingle pas
une plage entièrement antérieure au jeu de données, et un second contrôle exige
que les images du guide et le plan de capture se recouvrent exactement — sans
quoi le premier se contournerait en publiant une image hors plan.

Deux écarts majeurs du même tour ont été corrigés avec la même méthode :

- **M1-E5** ouvrait sur « établissez le nombre de machines distinctes », geste
  qu'aucun objectif de M1 n'enseigne, qui n'est pas la réponse notée et que la
  solution ne débriefait pas : un orphelin. La consigne demande maintenant la
  base de travail réellement enseignée — la présence du champ — et renvoie
  explicitement le décompte à **M2-E4**, qui l'enseigne avec ses limites.
- Le **quiz** plaçait la bonne réponse au rang 2 pour treize questions sur
  dix-sept et au rang 3 pour les quatre autres : jamais la première ni la
  dernière position. Cocher systématiquement la deuxième proposition rapportait
  13/17, soit 76 %, sans rien savoir. Les positions ont été permutées — 4, 4, 4
  et 5 — sans toucher aux textes, et
  `test_les_bonnes_reponses_du_quiz_ne_sont_pas_toujours_au_meme_rang` refuse
  qu'un rang ne soit jamais correct ou qu'il dépasse le tiers des questions.

Enfin, en corrigeant, deux défauts de la même famille sont apparus. La fiche de
contexte affichait le nombre d'hôtes de l'inventaire — vingt et un, qui EST la
réponse attendue de trois exercices, et qui n'était devenu cette réponse qu'à
la faveur d'une correction du tour précédent. Et `outils/fuites.py` ignorait les
petits entiers, par construction : « 21 » seul se rencontre partout. Il les
cherche désormais quand le nom qu'ils qualifient les suit — « 21 machines » est
attrapé, « 21 » nu reste ignoré — avec une table de synonymes, puisque le guide
écrit « machines » là où le manifeste dit « hôtes ».

### Le troisième passage : 11,8/20, et pourquoi la note baisse

Le troisième tour a été mené autrement. Neuf relecteurs, un par critère de la
grille de SPEC §11 plus un axe transverse sur les interdits de CLAUDE.md ; et,
derrière chacun, un contre-expert dont la consigne n'était pas de valider mais
de **réfuter** — rouvrir le fichier à la ligne citée, relancer la commande,
requalifier la gravité à la hausse comme à la baisse. Cinq écarts sur
cinquante-trois sont tombés à cette épreuve, dont un que le premier relecteur
avait classé bloquant.

Ce tour a surtout regardé ailleurs. Les précédents lisaient des fichiers :
celui-ci a ouvert les images en pleine résolution, lancé Chromium sur le guide,
injecté axe-core, mesuré des contrastes, rejoué les requêtes contre le lab et
recompté les contrôles annoncés. La note passe de 16,5 à **11,8/20**. Ce n'est
pas le kit qui a régressé ; c'est la relecture qui a atteint ce que les deux
premières ne touchaient pas.

Quarante-huit écarts tiennent : **2 bloquants, 23 majeurs, 23 mineurs**.

**Premier bloquant.** Une consigne de M1 écrivait « Reprenez vos **six** valeurs
de event.dataset ». Six EST `R.nb_sources`, la réponse attendue de M0-E2, de
M4-E1 et de M5-E2. Le garde ne l'a pas vu parce qu'il ancre les petits nombres
sur le sujet du libellé et ses synonymes : « six sources » était attrapé, « six
valeurs » non — et « valeurs » n'est le synonyme de rien, il est trop courant
pour être surveillé seul. Le garde s'ancre désormais aussi sur le NOM DU CHAMP
que porte la requête de contrôle de la réponse : un nombre isolé suivi, à trois
mots près, de « event.dataset » parle bien du décompte en question.

**Second bloquant : ce document.** Le tableau de synthèse annonçait « 94
contrôles, zéro échec » quand la seule exécution qu'il affichait en comptait
91. C'est la récidive exacte de la faute dont le kit avait tiré sa règle en P8.
Le tableau a été refait sur la sortie réelle de la campagne qui suit ces
corrections, et non sur un recomptage des fichiers de test.

**Ce que le tour a trouvé de plus instructif.** Cinq des dix exercices du
capstone validaient une empreinte que le stagiaire avait déjà produite le matin.
Trois par réemploi de clé. Deux par COLLISION D'EMPREINTE, que rien ne
surveillait : `R.source_la_moins_volumineuse` valait « ids.alert » et
`S5.source` aussi ; `R.source_ports_hauts` valait « firewall.traffic » et
`S6.source` aussi. Deux clés distinctes, deux exercices distincts, une seule
empreinte — le contrôle voisin comparait les clés et ne pouvait rien voir.

La correction a buté sur une contrainte arithmétique qu'il faut écrire, parce
qu'elle limite le jeu : avec six sources, trois portent déjà une réponse de
repère et une quatrième porte les événements de deux scénarios. Déplacer les
deux scénarios de collecte sur les deux sources restantes a fait apparaître le
revers — l'une d'elles est nommée dans les exemples de KQL du module M1, et en
faire une réponse rendait le garde de fuite inexploitable. La source muette a
donc changé de jeu, et c'est M4-E7 qui a changé de question : il ne valide plus
le nom de la source du trou mais **l'heure à laquelle la collecte reprend**, que
seul l'écran de santé donne.

Trois exercices du capstone n'ont plus d'empreinte du tout : on y construit un
écran, ou on y rédige cinq lignes. Leur en donner une revenait à leur faire
valider une valeur trouvée ailleurs — l'empreinte était là, et elle ne mesurait
rien. Ils déclarent désormais `rendu` : ce qui est remis, et comment le
formateur le juge. Le contrôle l'accepte à la place d'une réponse, et l'exige :
ni renvoi ni rendu reste un défaut.

**Et deux contrôles qui regardaient la mauvaise source.** En déplaçant la source
muette, deux tests ont continué d'interroger l'ancienne, écrite en dur. L'un a
échoué en annonçant « silence de 0 min » : il mesurait le silence d'une source
qui parle. Ils lisent maintenant le manifeste, qui dit où regarder. C'est la
leçon du tour, et elle vaut pour tout le kit : un contrôle qui écrit en dur ce
que le générateur choisit ne vérifie pas le kit, il vérifie une copie de lui.

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
   Kibana affiche « Impossible d’extraire les résultats de recherche ». Le piège
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
| E10 | SPEC §1 annonce « 6 h de parcours » ; mesuré lecture des corps et rappel actif compris, il vaut **6 h 47** | Mineur | Assumé et consigné : SPEC §1 ne budgète ni la lecture ni le rappel, que la charte rend obligatoires. Le kit garde son contenu et dit la vraie durée ; le guide du formateur donne deux formules, dont une en quatre séances |
| E11 | La source muette et celle du trou de collecte sont les mêmes au parcours et à l'épreuve | Mineur | Assumé et consigné : avec six sources, trois portent une réponse de repère et une quatrième les événements de deux scénarios — il ne reste qu'un choix possible de chaque côté. Le document du stagiaire le lui dit, et la première question de l'épreuve demande en plus l'heure de reprise, que le générateur tire à neuf |
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
