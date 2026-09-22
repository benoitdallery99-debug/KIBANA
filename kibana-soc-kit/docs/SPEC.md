# SPEC — Kit de formation pratique Kibana pour analystes SOC

Version 1.1 — 21/09/2026. Document de référence : toute divergence entre le dépôt et ce document est
corrigée, ou consignée et justifiée dans `docs/JOURNAL.md`. Le déroulé est dans `docs/ORCHESTRATION.md`.

## 1. Finalité

Rendre des analystes SOC autonomes sur l'usage opérationnel de Kibana — rechercher (Discover/KQL),
visualiser (Lens), construire et maintenir des tableaux de bord — par la pratique, sur un lab
reproductible.

Double exigence :
- **Pédagogique** : un débutant atteint les objectifs du §2 en une journée, avec formateur ou en
  autonomie guidée.
- **Opérationnelle** : le kit laisse des objets réutilisables — dashboards « Santé de la collecte » et
  « Vue IDS », fiche mémo, lab réinitialisable pour l'intégration de chaque nouvel arrivant.

Public : analystes SOC N1/N2, à l'aise avec les notions de journaux, IP, ports et authentification,
sans pratique de Kibana. Durée : 6 h de parcours + 45 min d'évaluation, découpable en 3 séances de 2 h.

## 2. Objectifs pédagogiques

Objectif général : à partir d'une question d'enquête, trouver et démontrer la réponse dans Kibana, puis
la rendre durable sous forme de visualisation et de tableau de bord partagé.

Chaque module formule ses objectifs en « À l'issue du module, le stagiaire est capable de… » avec un
verbe observable (identifier, filtrer, construire, justifier…). Chaque objectif est évalué par au moins
un exercice ET une question du quiz ; la matrice objectifs × exercices × questions figure dans le guide
formateur et un script vérifie sa complétude.

## 3. Architecture

### 3.1 Deux mondes à ne pas confondre

| | Chaîne de fabrication | Livrable |
|---|---|---|
| Où | PC du concepteur, en ligne | Poste ou VM cible, hors ligne |
| Contient | Claude Code, Playwright + Chromium, WeasyPrint, accès à la doc | Lab podman, guide HTML, PDF, ndjson, scripts |
| Règle | peut télécharger | ne télécharge jamais rien |

### 3.2 Arborescence

```
kit.config.yaml   paramètres (seule source de vérité)
Makefile
README.md         démarrage formateur en trois commandes
lab/              pod.yaml (podman kube play), config ES/Kibana, init/, preflight.sh, reset.sh
data/             generateur/ (Python), templates/ (index templates), manifest.json (généré)
parcours/         M0..M5 : Markdown + frontmatter YAML (objectifs, durée, exercices)
corriges/         dashboards : ndjson (+ JSON API Dashboards si version ≥ 9.5)
guide/            build.py (Jinja2), gabarits, styles, polices (fichiers officiels OFL), js (vanilla)
captures/         produites par Playwright — jamais retouchées à la main
verif/            pytest + Playwright (e2e/), audits guide et PDF
formateur/        guide formateur, quiz, épreuve pratique, fiche d'évaluation à chaud
docs/             SPEC, ORCHESTRATION, PLAN, JOURNAL, capacites, CHARTE_REDACTION, DESIGN,
                  NOTE_DE_CONCEPTION, RAPPORT_RECETTE
dist/             archive livrable (générée, gitignorée)
```

## 4. Lab

### 4.1 Pile
- Un pod `podman kube play` : Elasticsearch (nœud unique) + Kibana, images officielles
  `docker.elastic.co` en `stack.version`, épinglées par digest ; `imagePullPolicy: Never` en
  exploitation hors ligne (aucune tentative de téléchargement).
- Heap Elasticsearch fixé (par exemple 2 Go) et documenté. Volumes nommés (PersistentVolumeClaim)
  plutôt que montages hôte (SELinux, UID).
- Authentification activée ; mots de passe générés à l'installation dans `.env`. Kibana se connecte avec
  `kibana_system` (depuis 8.0, le superutilisateur `elastic` lui est interdit), mot de passe fixé par
  l'init.
- Clés de chiffrement Kibana générées à l'installation (`kibana-encryption-keys generate`) : sans
  `xpack.encryptedSavedObjects.encryptionKey`, l'alerting de M5 est indisponible. Vérifier dans la doc de
  la version les autres prérequis de l'alerting (TLS entre Kibana et Elasticsearch le cas échéant) et
  les satisfaire ; sinon, HTTP sans TLS toléré dans le lab, écart documenté dans le guide formateur.
- `xpack.license.self_generated.type: basic` ; test : `GET _license` renvoie `basic`.
- Réplicas à 0 (nœud unique) : santé `green`.
- Kibana : langue = `kibana.locale` (`i18n.locale` ou `i18n.defaultLocale` selon la version) ;
  `map.includeElasticMapsService: false` (sinon Lens et Maps attendent un service en ligne) ;
  télémétrie et newsfeed désactivés.
- Autres réglages Kibana laissés par défaut, y compris la plage de temps par défaut courte : c'est un
  piège réel, enseigné en M0.

### 4.2 Pré-vol (`lab/preflight.sh`)
Vérifie podman et sa version, `vm.max_map_count` ≥ 262144, RAM et disque libres (seuils documentés),
ports libres, présence locale des images (mode hors ligne). Sur macOS et Windows, podman tourne dans
une VM (podman machine) : `vm.max_map_count` et la RAM (souvent 2 Go par défaut, en prévoir au moins 6)
se règlent dans cette VM. Chaque échec affiche quoi faire, pas seulement ce qui ne va pas ; toute
commande sudo est affichée pour l'humain, jamais exécutée.

### 4.3 Initialisation (idempotente)
- Space `formation` avec vue de solution = `kibana.vue_solution` (8.16+ : elle change toute la navigation).
- Rôles et comptes : `formateur` (tous droits sur le Space), `stagiaire` (lecture des données, écriture
  des objets du Space).
- Data views à ID fixe : `donnees.data_view_id` (motif `donnees.data_view_motif`) et
  `epreuve.data_view_id` (motif `epreuve.data_view_motif`), champ temporel `@timestamp`.
- Aucun dashboard préinstallé hors corrigés (importables à la demande).

### 4.4 Réinitialisation
`make lab-reset` : supprime les objets créés par les stagiaires, régénère et recharge les données
réancrées sur l'instant présent, rejoue l'init. Cible : moins de 5 minutes. À lancer avant chaque
session, les données étant en fenêtre glissante.

### 4.5 Capacités à qualifier (P0 puis P1) → `docs/capacites.md`
Pour `stack.version` en licence Basic, avec URL de la doc officielle puis résultat du test dans le lab :
- API Dashboards (preview 9.4, GA 9.5) et export « dashboards API-compatible JSON »
- ES|QL dans Discover et dans Lens
- contrôles de dashboard (liste d'options, plage, time slider, contrôles ES|QL)
- sections repliables, panneau Liens, panneau Markdown
- drilldowns (dashboard → dashboard, URL) et licence requise
- passage d'un panneau de dashboard vers Discover
- formules Lens, lignes de référence
- export CSV ; rapports PDF/PNG (attendu : indisponibles en Basic)
- types de règles d'alerte disponibles, connecteurs (attendu : Index, Server log), règle Custom threshold
  avec alerte « no data » par groupe
- privilèges par Space
- terminologie de la version : « Discover session » ou « saved search », « data view » ou « index pattern »

Une capacité absente n'apparaît pas dans le parcours, sauf dans un encadré « Hors licence Basic » quand
son absence surprendrait (exemple : export PDF d'un dashboard).

### 4.6 Isolation réseau
Le lab est prouvé fonctionnel sur un réseau podman `--internal`, sans accès extérieur. Si ce réseau
empêche la publication de ports vers l'hôte, les contrôles s'exécutent depuis un conteneur rattaché au
même réseau. Le test prouve aussi qu'une requête vers l'extérieur échoue.

## 5. Données synthétiques

### 5.1 Principes
- Déterministes (graine `donnees.graine`) et ancrées sur l'instant du chargement : fenêtre de
  `donnees.fenetre_jours` jours se terminant à T0. Les réponses attendues sont des valeurs (IP, compte,
  domaine, nombre, durée), jamais des dates absolues.
- Rythme métier défini dans le fuseau `donnees.fuseau_metier`, horodatages stockés en UTC.
- ECS strict (`ecs.version` renseigné). Une data stream par source : `logs-<source>.<type>-<namespace>`
  (pas de tiret dans le dataset).
- Templates d'index explicites, de priorité supérieure aux templates intégrés, mappings typés : `ip` pour
  les adresses, `keyword` pour les identifiants, `date`, `long`. Afficher et contrôler le mapping effectif
  de chaque champ utilisé par le parcours, ainsi que le `index.mode` effectif.
- Ingestion par `_bulk` avec l'action `create` (seule acceptée par les data streams). Client Python
  `elasticsearch` de la même version majeure que le serveur, ou appels REST directs.
- Réalisme : environ 20 hôtes et 50 comptes, rythme ouvré (pics 8 h–19 h, week-end creux), bruit bénin
  (erreurs de mot de passe, NXDOMAIN, 404), 300 000 à 1 000 000 de documents au total.
- Aucune valeur réelle : IP externes en 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24 (RFC 5737),
  internes en RFC 1918, domaines en `.test` ou `.example` (RFC 2606), personnes fictives.
- Le jeu `epreuve` (graine et namespace dédiés) a les mêmes structures et des réponses différentes.

### 5.2 Sources et champs ECS minimaux

| Source | Champs clés |
|---|---|
| Authentification Windows | `event.code` (4624, 4625, 4740), `event.category: authentication`, `event.outcome`, `user.name`, `user.domain`, `source.ip`, `host.name` |
| Authentification SSH | `event.outcome`, `user.name`, `source.ip`, `host.name`, `process.name` |
| Alertes IDS | `event.kind: alert`, `event.category: [network, intrusion_detection]`, `rule.name`, `rule.id`, `event.severity`, `source.ip/port`, `destination.ip/port`, `network.transport`, `observer.type: ids` |
| DNS | `dns.question.name`, `dns.question.type`, `dns.response_code`, `source.ip`, `destination.ip` |
| Proxy | `url.domain`, `url.path`, `http.request.method`, `http.response.status_code`, `source.ip`, `destination.ip`, `source.bytes` (sortant), `destination.bytes` |
| Pare-feu | `event.action` (allow/deny), `network.transport`, `source.ip`, `destination.ip`, `destination.port` |

### 5.3 Scénarios cachés

| ID | Scénario | Réponses attendues |
|---|---|---|
| S1 | Force brute externe puis succès sur un compte de service | IP source, compte, nombre d'échecs avant le succès, hôte ciblé |
| S2 | Balayage de ports interne (moins de 3000 ports distincts, fenêtre de 10 min) | IP source, nombre de ports distincts |
| S3 | Beaconing périodique (période fixe ± gigue) vers un domaine `.test` | hôte, domaine, période en minutes |
| S4 | Exfiltration nocturne via le proxy (`source.bytes` anormal) | hôte, destination, volume en Mo arrondi |
| S5 | Trou de collecte de 2 h au milieu de la fenêtre sur une source | source, durée |
| S6 | Source muette depuis 2 h au moment du chargement | source |
| S7 | Leurre : scanner de vulnérabilités autorisé générant des échecs massifs | verdict « faux positif » + élément de contexte qui le prouve |

Le générateur écrit `data/manifest.json` : pour chaque scénario, réponses, type (ip, texte, entier,
entier ± tolérance, choix), règle de normalisation et requête DSL de contrôle. Le guide n'embarque que
les empreintes SHA-256 des réponses normalisées.

### 5.4 Contexte fictif de l'organisation
Une fiche « contexte » dans le guide, comme en SOC réel : nom d'organisation fictif, plan d'adressage et
rôle des sous-réseaux, serveurs critiques, comptes de service, IP du scanner de vulnérabilités autorisé
(clé de S7). Aucune ressemblance avec une organisation existante.

## 6. Parcours

### 6.1 Principes pédagogiques (explicités et justifiés dans le guide formateur)
- **Exemple travaillé puis guidage dégressif** : démonstration commentée → exercice guidé (étapes
  données) → semi-guidé (objectif + indices) → autonome (question seule). Le capstone M4 est autonome.
- **Rappel actif** : chaque module s'ouvre sur 2 à 3 questions de rappel du module précédent.
- **Une question d'enquête par exercice** : la réponse se prouve (requête + visualisation), elle ne se
  devine pas. Un exercice dont la réponse est trouvable sans faire l'exercice est un défaut.
- **Charge cognitive maîtrisée** : une notion nouvelle par étape ; vocabulaire exact de la version ;
  glossaire.
- **Anatomie d'un exercice** : identifiant, objectif, contexte SOC, consignes, indices à deux niveaux,
  champ de réponse, solution commentée (pourquoi, erreurs typiques), lien vers la doc de la version.

### 6.2 Modules (durées indicatives)

**M0 — Prise en main (30 min).** Kibana et Elasticsearch en un schéma (index, data stream, mapping,
types keyword / text / ip / date) ; Spaces et vue de solution ; data view ; sélecteur de temps
(relatif, absolu, rafraîchissement) ; navigation.

**M1 — Rechercher avec Discover (75 min).** Barre latérale des champs et valeurs principales ; table des
documents ; KQL : égalité, booléens, jokers, comparaisons, existence, CIDR sur champ ip, casse sur
keyword contre analyse du text ; filtres (épingler, inverser, désactiver) ; KQL, Lucene, et ES|QL si la
version le propose ; enregistrement de la recherche ; documents environnants.

**M2 — Visualiser avec Lens (60 min).** Choisir la visualisation selon la question (comparer, suivre une
évolution, répartir, distribuer) ; métrique, barres, lignes, tableau, heatmap ; valeurs principales et
leur approximation possible sur plusieurs shards ; unique count et son approximation (HyperLogLog++,
seuil de précision par défaut 3000) ; histogramme de dates et intervalle ; formules ; lignes de
référence ; couleur par valeur.

**M3 — Construire un tableau de bord (60 min).** Panneaux et grille ; contrôles ; interactions (un clic
= un filtre) ; plage de temps par panneau ; paramètres du dashboard ; enregistrement, partage, tags,
copie vers un Space. Règles de conception : un dashboard = un public + une question ; indicateurs clés
en haut à gauche ; au plus 12 panneaux ; titres formulés en questions ; unités et couleurs cohérentes ;
pas de secteurs au-delà de 5 parts.

**M4 — Capstone SOC (90 min).** Construire (1) « Santé de la collecte » : volume par source dans le
temps, dernier événement vu par source, trous de collecte ; (2) « Vue IDS » : alertes par gravité dans
le temps, signatures principales, sources et destinations principales, tableau des dernières alertes
(avec passage vers Discover si cette capacité existe en Basic). Puis résoudre S1 à S7 et rédiger une
synthèse de 5 lignes pour un chef de salle (grille d'évaluation de la synthèse fournie).

**M5 — Industrialiser (30 min).** Export et import ndjson, compatibilité entre versions ; data views à
ID fixe (réutiliser les dashboards du lab sur la cible) ; API Dashboards si la version ≥ 9.5 ; règles
d'alerte possibles en Basic et détection de silence ; rôles et Spaces.

### 6.3 Pièges réels à faire rencontrer (constatés en lab)
Chaque piège est provoqué volontairement dans un exercice, puis repris dans la fiche mémo et le quiz :
- « 0 résultat » : vérifier d'abord data view active, plage de temps et langage (KQL ou Lucene).
- `[1025 TO *]` relève de Lucene, pas de KQL (échec silencieux constaté en lab) ; en KQL :
  `destination.port >= 1025`. Le guide montre le comportement réel de la version (capture).
- CIDR directement sur un champ ip : `destination.ip : "10.0.0.0/8"`.
- Existence : `champ : *` en KQL, `_exists_:champ` en Lucene.
- Ne jamais deviner une valeur : lire les valeurs principales du champ dans la barre latérale.
- « 0 champ disponible » : un filtre de type de champ actif masque la liste.
- La recherche globale de Kibana n'est pas la barre de requête de Discover.
- Plage de temps par défaut trop courte pour le jeu de données.

## 7. Guide interactif HTML

### 7.1 Exigences
- Un seul fichier `dist/guide.html`, zéro requête réseau (contrôlé par Playwright), ≤ 20 Mo, ouvert en
  `file://` sous Firefox et Chromium récents. JS vanilla sans dépendance, CSS et images inlinés
  (captures en WebP dans le HTML).
- Fonctions : sommaire persistant avec position courante ; progression par module (localStorage sous
  try/catch, dégradation propre si indisponible) ; bouton « Copier » sur chaque requête ; indices à
  dévoilement progressif ; validation des réponses par empreinte (SubtleCrypto, repli JS pur) avec un
  retour explicite sans révéler la solution ; solution commentée révélable ; recherche plein texte ;
  glossaire en infobulles accessibles ; thèmes clair et sombre (préférence système + bascule) ; feuille
  d'impression.
- Source unique : Markdown + frontmatter YAML dans `parcours/`, compilés par `guide/build.py` vers le
  HTML et vers le PDF.

### 7.2 Captures d'écran
Produites par Playwright contre le lab : viewport fixe, `deviceScaleFactor` 2, locale de
`kit.config.yaml`, fuseau Europe/Paris, thème clair, éléments variables masqués. Annotations numérotées
dessinées par script à partir des boîtes englobantes des éléments ciblés (`data-test-subj`) ; numéros =
numéros d'étapes ; texte alternatif décrivant l'étape. Sélecteurs relevés dans le lab et centralisés
dans un seul module. `make captures` régénère tout après une montée de version.

### 7.3 Direction visuelle
Processus imposé : plan de design d'abord (4 à 6 couleurs nommées en hexadécimal, rôles typographiques,
maquettes ASCII, principes), relu contre les clichés ci-dessous, consigné dans `docs/DESIGN.md`, puis
seulement le code. Critique sur captures (clair/sombre, ordinateur/mobile) avant de déclarer la phase
finie.

Proposition de départ, à challenger : un carnet d'enquête sobre. Le parcours est une séquence, la
numérotation porte donc du sens ; l'élément signature est la trace de l'enquête (progression S1 → S7).
Le guide ne doit pas imiter l'interface de Kibana : le stagiaire distingue instantanément « à lire » et
« à faire dans Kibana », grâce à un unique marqueur visuel réservé aux actions dans Kibana.
Typographie proposée : Atkinson Hyperlegible Next (texte) et Atkinson Hyperlegible Mono (requêtes),
familles conçues pour la lisibilité, sous licence OFL avec noms réservés : fichiers officiels embarqués
tels quels.

Plancher de qualité : RGAA 4.1 (≈ WCAG 2.1 AA) — contrastes ≥ 4,5:1, focus visible, navigation au
clavier, `prefers-reduced-motion`, région ARIA live pour les retours de validation ; lignes de moins de
80 caractères ; aucune animation décorative.

À éviter (défauts génériques) : fond crème et accent terre cuite ; noir et vert acide ; cartes arrondies
identiques à ombre grise ; étiquettes en capitales espacées au-dessus de chaque titre ; un seul mot mis
en exergue par titre ; flèches « → » accolées aux boutons.

Rédaction de l'interface : voix active, verbes simples, une action garde le même nom partout
(« Vérifier ma réponse » → « Réponse vérifiée ») ; un message d'erreur dit ce qui se passe et quoi faire.

## 8. Documents imprimables (WeasyPrint, même source que le HTML)
- `guide.pdf` : page de titre, sommaire avec numéros de page (`target-counter`), signets PDF, en-têtes et
  pieds courants, polices embarquées, exercices sans solutions (solutions en annexe).
- `fiche-memo.pdf` : A4 recto verso, lisible en noir et blanc. Recto : KQL (syntaxe, exemples SOC,
  équivalences Lucene, pièges du §6.3). Verso : quelle visualisation pour quelle question, check-list
  d'un bon dashboard, raccourcis.
- `guide-formateur.pdf` : déroulé minuté ; préparation (`make lab-reset`) ; principes pédagogiques du
  §6.1 et leur justification ; matrice objectifs × exercices × questions ; erreurs fréquentes et
  remédiations ; questions de débriefing ; adaptation débutant / confirmé ; dépannage du lab.
- `corriges.pdf` : solutions détaillées avec requêtes et captures.
- `note-de-conception.pdf` : voir `docs/ORCHESTRATION.md`, phase P8.

## 9. Évaluation
- Quiz de 15 questions couvrant tous les objectifs : version intégrée au guide (explication pour chaque
  réponse) et version imprimable sans réponses (corrigé dans le guide formateur).
- Épreuve pratique de 30 minutes sur le jeu `epreuve` : construire un dashboard répondant à trois
  questions d'un chef de salle ; grille critériée dans le guide formateur. L'épreuve n'embarque aucune
  réponse, même sous forme d'empreinte.
- Fiche d'évaluation à chaud (utilité perçue, rythme, clarté) imprimable.

## 10. Vérification (`make verif`)

Suites pytest, chacune lançable seule :

| Cible | Ce qui est prouvé |
|---|---|
| `verif-lab` | licence `basic`, santé `green`, Kibana disponible, locale et vue de solution conformes, fonctionnement sur réseau podman `--internal` (SPEC §4.6) |
| `verif-donnees` | volumes par source, mapping effectif et `index.mode`, présence de S1 à S7, trou (S5) et silence (S6) effectifs, déterminisme (même graine → mêmes réponses), jeu `epreuve` distinct |
| `verif-parcours` | chaque réponse du manifeste recalculée par requête DSL ; chaque requête KQL tapée dans Discover (Playwright) donne le nombre attendu ; chaque libellé d'UI cité existe dans le lab ; chaque exercice pointe une réponse du manifeste |
| `verif-corriges` | import dans un Space vierge sans erreur ni référence manquante ; chaque panneau rendu sans erreur ; valeurs affichées = manifeste |
| `verif-guide` | zéro requête externe ; axe-core injecté via Playwright, sans violation serious ou critical ; ≤ 20 Mo ; liens internes valides ; toutes les images ont un texte alternatif ; empreintes = manifeste |
| `verif-pdf` | polices embarquées (`pdffonts`), images toutes rendues, sommaire paginé, signets, aucune page blanche parasite |
| `verif-package` | `SHA256SUMS` valides ; installation depuis l'archive dans un répertoire vierge, réseau `--internal`, aucun téléchargement ; M0 rejoué par Playwright |

## 11. Grille de notation /20 (appliquée par le sous-agent `relecteur-expert`)

**Fond — 12 points**
- Exactitude technique vérifiée pour la version, la licence et la locale (3)
- Progression, objectifs mesurables, guidage dégressif (3)
- Exercices et scénarios SOC : réalisme, preuves, pièges, faux positif (3)
- Utilité opérationnelle : dashboards réutilisables, fiche mémo, guide formateur, réinitialisation (3)

**Forme — 8 points**
- Identité visuelle et lisibilité, captures annotées (3)
- Ergonomie du guide : navigation, validation, copie, progression, impression (2)
- Accessibilité et robustesse hors ligne (2)
- Langue et finition : orthotypographie française, cohérence terminologique (1)

Seuil de livraison : ≥ 18/20, aucun critère sous les deux tiers de ses points, zéro écart bloquant.

## 12. Déroulé
Voir `docs/ORCHESTRATION.md` (phases P0 → P8, critères de sortie, règles d'autonomie).

## 13. Hors périmètre (V2)
Application Elastic Security (règles de détection, Timeline), Machine Learning, Fleet et Elastic Agent,
Canvas, Vega, Maps, Watcher, un Space et un compte par stagiaire.

## 14. Références (à revérifier pour la version exacte)
- Dashboards as code : https://www.elastic.co/docs/explore-analyze/dashboards/manage-dashboards-as-code
- Spécification de l'API Dashboards : https://elastic.github.io/dashboards-api-spec/
- Annonce GA de l'API Dashboards (9.5) : https://www.elastic.co/search-labs/blog/dashboards-as-code-kibana-api
- Objets enregistrés, import et compatibilité : https://www.elastic.co/guide/en/kibana/current/managing-saved-objects.html
- Rapports et partage : https://www.elastic.co/docs/explore-analyze/report-and-share
- Connecteurs Kibana : https://www.elastic.co/docs/reference/kibana/connectors-kibana
- Niveaux de licence : https://www.elastic.co/subscriptions
- Spaces et vue de solution : https://www.elastic.co/docs/deploy-manage/manage-spaces
- Agrégation cardinality : https://www.elastic.co/docs/reference/aggregations/search-aggregations-metrics-cardinality-aggregation
- Casse de la fonction ES|QL KQL() : https://github.com/elastic/elasticsearch/issues/135772
- start-local (trial par défaut) : https://github.com/elastic/start-local
- Cartes hors ligne (EMS) : https://www.elastic.co/guide/en/kibana/current/maps-connect-to-ems.html
- Claude Code, bonnes pratiques et /goal : https://code.claude.com/docs/en/best-practices · https://code.claude.com/docs/en/goal
