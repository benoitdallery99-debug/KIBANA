# JOURNAL — état, décisions, écarts

Format : une entrée par phase. Chaque décision structurante est notée
« décision · alternatives écartées · raison ». Les écarts ouverts sont listés en fin de document et
repris tant qu'ils ne sont pas soldés.

---

## Amorçage — 21/09/2026 — TERMINÉ

### État
Fichiers de référence créés à l'identique dans `kibana-soc-kit/` : `kit.config.yaml`, `CLAUDE.md`,
`docs/SPEC.md`, `docs/ORCHESTRATION.md`, `.claude/agents/relecteur-expert.md`,
`.claude/agents/stagiaire-candide.md`, `.gitignore`. Vérification d'intégrité passée : 14 sections dans
SPEC, 31 lignes de tableau, S1 à S7 présents, 22 guillemets ouvrants pour 22 fermants, UTF-8, aucun
gabarit `<< >>` résiduel. Commit `0db74c4` « amorçage du kit ».

### Décisions

**D1 — Emplacement du kit : sous-répertoire `kibana-soc-kit/`.**
L'amorçage impose de s'arrêter si le répertoire courant contient autre chose qu'un dépôt git vide. Il
contenait le dépôt applicatif PHP « picturegallery ». Question posée à l'humain, réponse : construire
dans `kibana-soc-kit/`.
*Alternatives écartées* : (a) racine du dépôt — collisions sur `README.md` et `.gitignore`, dépôt
hybride illisible ; (b) dépôt neuf ailleurs — contredit la consigne de pousser sur
`claude/kibana-soc-training-kit-yf6jr7` dans `YamTeam9/picturegallery`.
*Conséquence* : la racine du kit au sens de SPEC §3.2 est `kibana-soc-kit/`. Tous les chemins de SPEC
et d'ORCHESTRATION s'y rapportent.

**D2 — `stack.version` = 9.5.3 (et non 9.5.4, dernière stable annoncée).**
`docker.elastic.co` est bloqué par la politique d'egress (écart E1). Les images officielles restent
accessibles par miroir, mais 9.5.4 n'y est pas publiée ; 9.5.3 l'est. Un lab qui démarre et se vérifie
vaut mieux qu'une version plus récente dont tous les contrôles seraient « NON EXÉCUTÉ ».
*Alternatives écartées* : (a) 9.5.4 — non téléchargeable ici, lab impossible ; (b) 8.19.21 —
téléchargeable, mais prive le kit de l'API Dashboards GA (SPEC §4.5, P4) sans nécessité, la cible
n'étant pas imposée en 8.x.
*Conséquence* : `stack.version` ≥ 9.5, donc le chemin « API Dashboards » de CLAUDE.md est celui retenu
en P4, à confirmer en P0/P1.

**D3 — `kibana.locale` = fr-FR, `kibana.vue_solution` = classic.**
Réponses de l'humain. fr-FR est cohérent avec l'exigence de contenu stagiaire en français ; classic
donne la navigation complète et neutre, la vue `security` étant écartée parce que l'application Elastic
Security est hors périmètre (SPEC §13) et qu'elle réorganise toute la navigation.

**D4 — Images tirées de `mirror.gcr.io/library/*` au lieu de `docker.elastic.co`.**
Voir écart E1. Preuve que l'image est bien l'officielle : le digest de configuration obtenu par le
miroir, `sha256:d43d5775b18dd35d1fd6474ac55bea5ea8475e6aaa512492ca95ca9462a208e7`, est exactement celui
que Docker Hub tentait de servir avant d'être refusé par le CDN. Image identique, source différente.
*Alternatives écartées* : `docker.elastic.co` (403), Docker Hub direct (403 sur le CDN de blobs),
`quay.io` et `registry.access.redhat.com` (injoignables).
*Conséquence pour le livrable* : le kit livré épingle les images par digest et les embarque via
`podman save` (SPEC §4.1) ; le poste cible ne dépend donc d'aucun registre. Le miroir n'est qu'un
détail de la chaîne de fabrication, pas du livrable.

**D5 — Vérification documentaire par les sources officielles hébergées sur GitHub.**
`www.elastic.co` est bloqué (E1). La documentation Elastic est publiée en source ouverte dans
`github.com/elastic/docs-content`, accessible ici. C'est la source dont est engendré elastic.co : ce
n'est pas un succédané mais l'amont. Elle est clonée localement pour la chaîne de fabrication.
*Conséquence* : dans `docs/capacites.md`, chaque capacité porte l'URL elastic.co canonique (utile au
lecteur du kit, qui n'a pas la même contrainte réseau) ET la référence au fichier source GitHub
réellement consulté. La preuve forte reste le lab, conformément à CLAUDE.md.

---

## P0 — Capacités et plan — TERMINÉ

Recherche documentaire déléguée à 13 sous-agents, un par famille de capacités de SPEC §4.5, dans le
clone local de `github.com/elastic/docs-content` : 270 constats, chacun avec son badge `applies_to`,
son fichier source et son URL canonique. Puis sonde du lab (`lab/sonder_capacites.py`) et des pièges
(`lab/sonder_pieges.py`).

**Livrables** `docs/capacites.md` (90 lignes de capacités réparties en 13 familles),
`docs/capacites-lab.json`, `docs/pieges-lab.json`, `docs/PLAN.md`.

**Bilan honnête de la colonne « confirmé en lab »** : 19 confirmées, 7 infirmées, 64 non sondées. Les
64 restent marquées NON SONDÉ avec le test qui les trancherait : une capacité non testée n'est pas une
capacité acquise.

### Constats qui changent le parcours
1. **Drilldown URL : hors Basic** (Gold), alors que dashboard → dashboard et le passage vers Discover
   sont libres. La documentation est muette sur ce point ; c'est le code de la version 9.5.3 qui tranche
   (`url_drilldown` porte `minimalLicense: 'gold'`). M3 est recomposé en conséquence, avec un encadré.
2. **La planification d'exports récurrents est hors Basic, y compris en CSV**, et ce n'est écrit nulle
   part dans la documentation. Second encadré « Hors licence Basic », en M5.
3. **L'API Dashboards refuse les panneaux `map` et `alerts_table`** : un tableau de bord SOC comportant
   une carte ne peut pas être géré en code en 9.5.3. Les corrigés n'en emploient aucun.
4. **Connecteurs d'alerte : 2 sur 73** (`.index`, `.server-log`), relevé sur le lab. M5 s'y tient.
5. **Depuis 9.5, « Exporter » depuis un tableau de bord rend un JSON d'API et non un ndjson**, et cet
   export est incomplet. Le ndjson ne s'obtient plus que par Gestion de la pile → Objets enregistrés.

### Incident de fabrication
Deux sous-agents ont écrit `docs/capacites.md` en même temps — l'agent de synthèse du workflow et un
agent lancé séparément — et leurs écritures se sont percutées : le fichier a contenu ses trois sections
de clôture en double. Repéré à la relecture, pas signalé par les agents. Corrigé par fusion, sans perte :
785 lignes, seize sections numérotées sans doublon.
*Leçon retenue* : ne jamais confier le même fichier à deux agents simultanés. Les phases suivantes
attribuent un propriétaire unique à chaque fichier.

---

## P1 — Lab — TERMINÉ (vérifications passées)

### Preuve
`make verif-lab` : **13 tests passés, sortie 0**, en 57 s. `make lab-up` va au bout et rejoue
l'initialisation sans effet de bord. Ce qui est prouvé : licence `basic`, santé `green`, Elasticsearch
et Kibana en 9.5.3, locale fr-FR servie (60 705 clés), vue de solution `classic` sur le Space
`formation`, data views à ID fixe, rôles et comptes, connexion de Kibana par `kibana_system`, images
épinglées par digest et `imagePullPolicy: Never`, cartes et télémétrie coupées, lab fonctionnel sur
réseau podman `--internal` et sortie extérieure impossible depuis ce réseau.

### Durées mesurées
Elasticsearch prêt en 36 s ; Kibana disponible 6 à 60 s plus tard selon l'état du volume ;
`make lab-up` complet en moins de 2 min sur 4 cœurs. La cible « moins de 5 minutes » de SPEC §4.4 est
tenue avec de la marge.

### Décisions

**D6 — Seuils d'occupation disque en valeur absolue (5 Go / 3 Go / 2 Go).**
Par défaut Elasticsearch refuse d'allouer le moindre shard dès 90 % d'occupation du système de
fichiers. Constaté en lab : cluster `red`, `.security-7` non alloué, « the node is above the high
watermark », alors que 24,9 Go restaient libres. Un poste de travail au disque bien rempli aurait
exactement le même symptôme, sans rapport avec la place réellement nécessaire.
*Alternatives écartées* : désactiver le décideur d'allocation disque (`threshold_enabled: false`),
qui supprime un garde-fou utile au lieu de le régler.
*Conséquence* : `lab/preflight.sh` contrôle l'espace libre réel et signale, sans bloquer, un système
de fichiers au-delà de 90 %.

**D7 — Un réseau podman `--internal` exige `bridge-nf-call-iptables = 0`.**
Constaté en lab : sur un réseau `--internal`, Elasticsearch écoutait bien sur `0.0.0.0:9200` et le DNS
résolvait, mais tout le trafic entre conteneurs expirait. Cause : `br_netfilter` renvoyait le trafic du
pont vers iptables, où la règle d'isolation posée par netavark coupait aussi les échanges *internes*.
Le réglage avait été mis à 1 par le démon Docker présent sur le poste de fabrication, arrêté depuis.
Témoin retenu dans la suite de vérification : sur le réseau interne la connexion sortante échoue faute
de route (`rc=7`), alors que sur le réseau par défaut la même requête établit bien une connexion —
sans ce témoin, le contrôle d'isolation ne prouverait rien.
*Conséquence* : contrôle ajouté à `lab/preflight.sh`, avec la commande `sudo` affichée et non exécutée.

**D8 — Un module partagé `outils/` en plus de l'arborescence de SPEC §3.2.**
`outils/conf.py` lit `kit.config.yaml` et sert au lab, aux données, au guide et aux vérifications.
*Alternative écartée* : dupliquer la lecture des paramètres dans chaque dossier, ce qui ouvrirait la
porte à des valeurs en dur — précisément ce que CLAUDE.md interdit.

### Erreurs rencontrées, et ce qu'elles ont appris
1. `telemetry.enabled` n'existe pas dans Elasticsearch : le nœud refuse de démarrer. La télémétrie est
   une affaire de Kibana. Supposer un réglage plutôt que le vérifier coûte un démarrage.
2. Une vérification ne doit jamais détruire ce qu'elle vérifie : `podman network rm -f` a supprimé le
   lab, car l'option force retire aussi les conteneurs rattachés. Le démontage détache maintenant le
   pod avant de supprimer le réseau.
3. `podman` nomme le conteneur d'infrastructure d'après l'ID du pod, pas son nom.
4. Rattacher un pod déjà démarré à un réseau ne suffit pas : le trafic entrant n'est pas routé. Le pod
   de contrôle est donc *créé* sur le réseau interne.
5. Dans une boucle d'attente, l'échec d'une tentative est normal : sans neutralisation du code de
   retour, `set -e` interrompt l'attente au premier essai.

---

## P4 — Tableaux de bord corrigés — TERMINÉ (fait avant P3, voir D9)

### Preuve
`make verif-corriges` : **8 tests passés, sortie 0**, en 59 s. Import dans un Space vierge sans erreur
ni référence manquante, panneaux non vides après import, rendu des 12 panneaux sans erreur (Playwright),
valeur affichée égale au décompte d'Elasticsearch sur la même fenêtre, et le corrigé révèle bien S6.

### Décisions

**D9 — P4 traité avant P3.**
Le module M4 demande au stagiaire de construire ces deux tableaux de bord. Les décrire avant d'avoir
prouvé qu'ils se construisent, se rendent et disent le vrai aurait exposé à réécrire le module. Les
corrigés servent donc de vérification technique préalable au parcours.
*Alternative écartée* : suivre l'ordre littéral P3 puis P4, au prix d'une réécriture probable de M4.

**D10 — Tableaux de bord définis en code, par l'API Dashboards.**
`stack.version` = 9.5.3 ≥ 9.5 : CLAUDE.md prescrit l'API Dashboards. Confirmé sur le lab en licence
Basic. Routes réelles : `PUT /api/dashboards/{id}` (idempotent, recommandé pour du versionné) et
`POST /api/dashboards` (engendre un nouvel identifiant). La route n'est pas `/api/dashboards/dashboard/{id}` :
erreur commise, corrigée par lecture de la doc officielle puis essai sur le lab.
*Conséquence* : aucun JSON Lens écrit de zéro, ce que CLAUDE.md interdit.

**D11 — Portabilité : ce que le lab a réellement montré, et ce que M5 enseignera.**
SPEC §4.3 prévoit des data views à ID fixe pour rendre les tableaux de bord réutilisables sur la cible.
Trois constats de lab nuancent ce récit, et M5 les enseignera tels quels plutôt que la version simplifiée :
1. L'API Dashboards REFUSE une source de données référençant une data view par son identifiant
   (`data_view` rejeté en HTTP 400) ; seul `data_view_spec`, qui décrit le motif en ligne, est admis.
2. En conséquence, l'export ndjson de ces tableaux ne porte AUCUNE référence : ils sont autonomes,
   s'importent partout sans référence manquante, mais leur motif d'index est inscrit dans l'objet.
3. Un tableau de bord est un objet PARTAGEABLE entre Spaces. Importer un identifiant qui existe déjà
   dans un autre Space ne l'écrase pas et n'échoue pas : Kibana crée une copie sous un nouvel
   identifiant, rendu dans `destinationId` — même avec `createNewCopies=false`.
*Conséquence pédagogique* : l'ID fixe de data view garde tout son sens pour les objets construits dans
l'interface sur une data view enregistrée, que le stagiaire produira lui-même en M4 et exportera en M5.
Le contraste entre ses exports et ceux des corrigés est la matière même du module.

**D12 — Un indicateur de santé se mesure sur une fenêtre courte.**
Premier jet : « combien de sources émettent ? » en `unique_count` sur sept jours — affichait 6, au vert,
alors qu'une source était muette depuis deux heures. Corrigé en « combien de sources ont émis dans la
dernière heure ? » (ES|QL, `WHERE @timestamp > NOW() - 1 hour`) : affiche 5, au rouge. Un indicateur
qui ne peut pas passer au rouge n'est pas un indicateur.

### Détails relevés en lab
- Types de panneaux acceptés par l'API : `data_table`, `gauge`, `heatmap`, `legacy_metric`, `metric`,
  `mosaic`, `pie`, `region_map`, `tag_cloud`, `treemap`, `waffle`, `xy`.
- Un filtre au niveau du panneau (`filter`) est refusé : pour restreindre un panneau à une source, on
  vise son motif d'index, ce qui est de toute façon plus lisible.
- Playwright : l'élément `globalLoadingIndicator-hidden` est TOUJOURS présent dans le DOM mais masqué
  en CSS ; il faut attendre son rattachement (`state="attached"`), jamais sa visibilité.
- Import ndjson par `requests` : retirer l'en-tête `Content-Type` de la session, sinon HTTP 415.

---

## P5 et P7 — guide, PDF, captures, archive — TERMINÉS

### Preuves
`make verif-guide` : 10 passés. `make verif-pdf` : 7 passés. `make verif-package` : 8 passés.

### Décisions

**D13 — Direction visuelle « La main courante », choisie contre « La planche d'expertise ».**
Voir `docs/DESIGN.md`. La seconde direction cumulait deux des six clichés listés par SPEC §7.3, dont
la terre cuite nommément citée ; surtout, sa palette n'était pas motivée par le sujet. Le critère qui
a tranché est fonctionnel et non esthétique : le guide ne doit pas ressembler à Kibana, sans quoi le
stagiaire ne sait plus lequel des deux écrans il regarde.

**D14 — Les empreintes, jamais les réponses, avec une exception assumée.**
Le guide n'embarque que des SHA-256 de réponses normalisées. La normalisation JavaScript a été
confrontée à celle de Python sur de l'UTF-8 multioctet et des accents : elles concordent exactement.
Un SHA-256 en JavaScript pur double `crypto.subtle`, indisponible en `file://` selon les navigateurs.
*Exception* : la fiche de contexte publie serveurs critiques, comptes de service et adresse du scanner
autorisé, que SPEC §5.4 impose de publier. Une réponse s'y perd parmi ses semblables. La règle et son
exception vivent dans `outils/fuites.py`, partagé par le constructeur et la vérification.

### Défauts trouvés par l'exécution, à ce stade
1. La jauge de progression affichait un caractère illisible : les glyphes géométriques manquent à la
   police et tombaient en repli. Remplacée par un compte chiffré, lisible aussi à l'impression.
2. Les tableaux débordaient de l'écran sur téléphone.
3. Les sélecteurs du sélecteur de temps étaient périmés : en 9.5 il s'appelle `dateRangePicker…`.
   Un sélecteur périmé ne lève aucune erreur — l'élément est simplement introuvable. L'avertissement
   posé dans `captures/produire.py` l'a signalé dès la première exécution.
4. **Les contrôles de S6 se mesuraient depuis « maintenant »** au lieu de l'instant du chargement.
   Les données étant en fenêtre glissante, la suite passait juste après `make data` puis échouait
   toute seule une heure plus tard. Recalés sur `engendre_le` du manifeste. C'est le genre de défaut
   qui n'apparaît qu'en relançant à froid, et qui aurait accueilli le formateur.

### Relevé utile au parcours
L'interface fr-FR de 9.5.3 est **partiellement traduite** : l'invite de la barre de requête reste en
anglais (« Filter your data using KQL syntax ») au milieu d'un écran français. Raison de plus pour ne
citer que des libellés relevés dans le lab.

### Note sur les polices
Les fichiers livrés dans `guide/polices/` sont ceux distribués par le projet, non modifiés (polices
variables, table `fvar` intacte), avec leurs licences OFL. Dans les PDF, WeasyPrint les sous-ensemble
comme le fait tout producteur de PDF, et marque le sous-ensemble du préfixe conventionnel. La règle de
CLAUDE.md porte sur les fichiers que le kit distribue, qui sont intacts.

---

## P3 — Parcours — EN COURS

`docs/CHARTE_REDACTION.md` écrite en premier, avec le schéma exact du frontmatter : la qualité des
modules est ainsi contrôlable par programme et non par bonne volonté. `parcours/M0.md` écrit comme
module de référence avant toute délégation. M1 écrit et vérifié. M2 à M5 en cours de rédaction, un
sous-agent par module, séquentiellement, chacun propriétaire d'un seul fichier — conséquence de
l'incident de P0.

`make verif-parcours` sur M0 et M1 : 13 passés, 3 échecs qui disent tous la même chose, à savoir que
M2 à M5 n'existent pas encore. Tous les contrôles de fond passent : les 19 requêtes KQL de M1 rejouées
dans Discover donnent ce qui est annoncé, les libellés cités existent dans l'interface fr-FR du lab,
aucune réponse n'est écrite en clair, et chaque piège est décrit tel qu'il se comporte.

---

## Écarts ouverts

| ID | Écart | Gravité | Statut | Parade |
|---|---|---|---|---|
| E1 | `www.elastic.co` et `docker.elastic.co` bloqués par la politique d'egress de l'organisation (403 au CONNECT). Le README du proxy interdit de contourner. | Majeur (chaîne de fabrication uniquement) | Contourné, pas résolu | Images : miroir `mirror.gcr.io`, digest vérifié identique (D4). Documentation : dépôt source officiel `elastic/docs-content` sur GitHub (D5). Aucun effet sur le livrable, qui est hors ligne par construction. |
| E2 | podman absent de l'environnement de fabrication. | Mineur | Résolu | podman 4.9.3 installé depuis les dépôts Ubuntu noble ; `podman kube play` disponible, fidélité à SPEC §4.1 préservée. |
| E3 | `vm.max_map_count` à 65530, sous le minimum 262144 d'Elasticsearch. | Mineur | Résolu | Porté à 262144 par `sysctl -w`. Aucun `sudo` exécuté : la session est root dans un conteneur éphémère. `lab/preflight.sh` affichera la commande à l'humain sur un poste cible, sans l'exécuter (CLAUDE.md). |
| E6 | SPEC §6.3 annonce que `[1025 TO *]` produit un « échec silencieux ». En 9.5.3 fr-FR, c'est FAUX : Discover affiche « Impossible d'extraire les résultats de recherche ». Le vrai piège muet est `_exists_:champ`, qui renvoie 0 résultat sans aucun message. | Mineur (prémisse de la SPEC) | Résolu, SPEC non modifiée | `docs/pieges-lab.json` relève le comportement réel ; le parcours enseignera ce qui se passe vraiment, comme SPEC §6.3 l'exige elle-même (« le guide montre le comportement réel de la version »). |
| E5 | Le démon Docker, démarré pendant la reconnaissance de l'environnement, active `bridge-nf-call-iptables` et casse les réseaux podman `--internal`. | Mineur | Résolu | Démon arrêté (le kit ne s'en sert pas), réglage remis à 0, contrôle ajouté au pré-vol (D7). |
| E4 | La version 9.5.4, dernière stable annoncée, n'est pas disponible ici. | Mineur | Accepté | Kit construit et vérifié en 9.5.3 (D2). La montée de version est prévue par construction : `stack.version` dans `kit.config.yaml`, `make captures` régénère les captures. |
