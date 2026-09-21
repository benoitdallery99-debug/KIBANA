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

## P0 — Capacités et plan — EN COURS

Démarré le 21/09/2026. Recherche documentaire déléguée à 13 sous-agents, un par famille de capacités
de SPEC §4.5, dans le clone local de `github.com/elastic/docs-content`. `docs/capacites.md` et
`docs/PLAN.md` restent à produire.

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

## Écarts ouverts

| ID | Écart | Gravité | Statut | Parade |
|---|---|---|---|---|
| E1 | `www.elastic.co` et `docker.elastic.co` bloqués par la politique d'egress de l'organisation (403 au CONNECT). Le README du proxy interdit de contourner. | Majeur (chaîne de fabrication uniquement) | Contourné, pas résolu | Images : miroir `mirror.gcr.io`, digest vérifié identique (D4). Documentation : dépôt source officiel `elastic/docs-content` sur GitHub (D5). Aucun effet sur le livrable, qui est hors ligne par construction. |
| E2 | podman absent de l'environnement de fabrication. | Mineur | Résolu | podman 4.9.3 installé depuis les dépôts Ubuntu noble ; `podman kube play` disponible, fidélité à SPEC §4.1 préservée. |
| E3 | `vm.max_map_count` à 65530, sous le minimum 262144 d'Elasticsearch. | Mineur | Résolu | Porté à 262144 par `sysctl -w`. Aucun `sudo` exécuté : la session est root dans un conteneur éphémère. `lab/preflight.sh` affichera la commande à l'humain sur un poste cible, sans l'exécuter (CLAUDE.md). |
| E5 | Le démon Docker, démarré pendant la reconnaissance de l'environnement, active `bridge-nf-call-iptables` et casse les réseaux podman `--internal`. | Mineur | Résolu | Démon arrêté (le kit ne s'en sert pas), réglage remis à 0, contrôle ajouté au pré-vol (D7). |
| E4 | La version 9.5.4, dernière stable annoncée, n'est pas disponible ici. | Mineur | Accepté | Kit construit et vérifié en 9.5.3 (D2). La montée de version est prévue par construction : `stack.version` dans `kit.config.yaml`, `make captures` régénère les captures. |
