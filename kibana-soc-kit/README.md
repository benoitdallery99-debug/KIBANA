# Kit de formation Kibana pour analystes SOC

Elastic Stack 9.5.3 · licence Basic · interface fr-FR · 100 % hors ligne

Un parcours pratique de 6 h 47 : six modules, 35 exercices, 27 objectifs, sur un
lab conteneurisé dont les données portent sept scénarios cachés — force brute
suivie d'un succès, balayage de ports, balise périodique, exfiltration nocturne,
trou de collecte, source muette, et un leurre pour punir la conclusion hâtive.

**Aucune réponse n'est écrite à la main.** Chacune vient du manifeste du
générateur et est recalculée par requête sur le lab. Changez la graine, les
réponses changent.

## Par où commencer

**Juste regarder** — ouvrez `dist/guide.html` dans un navigateur. Il s'ouvre
sans serveur et sans réseau : polices, captures et scripts sont embarqués. C'est
ce que voit le stagiaire.

**Comprendre le pourquoi** — `dist/note-de-conception.pdf`, puis
`dist/guide-formateur.pdf` pour le déroulé minuté et la matrice
objectifs/exercices/quiz.

**Savoir ce qui est prouvé** — `docs/RAPPORT_RECETTE.md` : 118 contrôles, ce
qu'ils démontrent, et les dix écarts assumés.

## Monter le lab

Deux chemins, selon ce que vous avez.

### Vous avez cloné ce dépôt (vous avez donc un accès réseau)

```bash
make lab-images     # tire les images Elasticsearch et Kibana par leur étiquette
make venv           # environnement Python
make lab-up         # pré-vol, démarrage du pod, initialisation des Spaces
make data           # engendre et charge 381 039 documents
```

Kibana répond ensuite sur http://localhost:5601. Les mots de passe sont
engendrés à l'installation dans `.env`, qui n'est jamais commité.

**N'allez pas tirer les images par empreinte à la main** : elles arriveraient
sans étiquette, et le pré-vol — qui les cherche par nom — les déclarerait
absentes alors qu'elles sont là. `make lab-images` fait les deux choses dans le
bon ordre.

### Vous avez l'archive hors ligne (1,4 Go)

Elle embarque les images, les roues Python et le générateur, pour une machine
sans aucun accès réseau. Suivez `INSTALLATION.md` à l'intérieur de l'archive.
Elle se reconstruit ici par `make package`.

### Sous macOS ou Windows

podman tourne dans une machine virtuelle, et c'est **elle** qu'il faut
dimensionner :

```bash
podman machine init --memory 8192 --disk-size 40
podman machine start
podman machine ssh 'sudo sysctl -w vm.max_map_count=262144'
```

Le pré-vol lit la mémoire de cette VM, pas celle de l'hôte : un Mac de 16 Go
avec une VM réglée à 2 Go ne fera pas tourner Elasticsearch.

**Faire tourner le lab demande 6 Go ; le vérifier en demande 12.** Un contrôle
de `make verif` monte un second pod complet sur un réseau isolé pendant que le
premier tourne. Sous les 12 Go, il s'annonce NON EXÉCUTÉ avec sa raison, et le
reste de la suite s'exécute. Pour l'exécuter vraiment :
`podman machine set --memory 12288`.

## Vérifier

```bash
make verif
```

118 contrôles, répartis en sept suites lançables séparément. Ils s'exécutent
**contre le lab vivant**, pas contre des fichiers : chaque requête du parcours
est rejouée dans Discover, chaque libellé cité est cherché dans l'interface
fr-FR, chaque chiffre publié est recompté.

## Ce qui est où

| Chemin | Quoi |
|---|---|
| `parcours/` | les six modules, frontmatter YAML + corps Markdown |
| `data/` | le générateur, ses scénarios, son manifeste de réponses |
| `lab/` | pré-vol, pod podman, initialisation des Spaces et des rôles |
| `guide/` | construction du HTML autonome et des sept PDF |
| `corriges/` | les deux tableaux de bord, définis en code |
| `formateur/` | déroulé, matrice, quiz, épreuve pratique |
| `captures/` | plan de capture et images, produites par Playwright |
| `verif/` | les 118 contrôles |
| `docs/` | spécification, charte de rédaction, relevé de capacités, journal |

`docs/JOURNAL.md` porte l'état, les décisions **et leurs raisons**, et les
écarts ouverts. C'est le fichier à lire avant de reprendre le travail.

## Règles du kit

- Données 100 % synthétiques : IP externes en RFC 5737, internes en RFC 1918,
  domaines en `.test`. Rien d'un système réel.
- Statuts honnêtes : un contrôle non exécuté est **non exécuté**, avec sa
  raison — jamais « passé ».
- Toute affirmation technique est vérifiée dans la documentation de la version,
  **puis** dans le lab. Une fonctionnalité absente du lab n'existe pas pour le
  parcours.
- Licence Basic uniquement. Le parcours n'enseigne que ce qui existe en Basic.
