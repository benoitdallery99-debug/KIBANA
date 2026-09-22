# Charte de rédaction du parcours

Ce document lie tous les modules. Un module qui s'en écarte est corrigé, pas discuté. Il est la
réponse à une question simple : *à quoi reconnaît-on un module du kit, et pas un tutoriel de plus ?*

Paramètres en vigueur : Elastic Stack **9.5.3**, licence **Basic**, interface en **fr-FR**, vue de
solution **classic**. Ce qui a le droit d'exister dans le parcours est listé dans `docs/capacites.md` ;
ce qui n'y figure pas n'existe pas pour le kit.

---

## 1. Ton

- **On s'adresse à un collègue, pas à un élève.** Le lecteur est analyste SOC : il connaît les
  journaux, les adresses, les ports, l'authentification. Il ne connaît pas Kibana. On ne lui explique
  donc pas ce qu'est une alerte ; on lui explique où Kibana la range.
- **Voix active, présent, phrases courtes.** « Ouvrez Discover », pas « Discover devra être ouvert ».
- **Pas de familiarité, pas d'enthousiasme de brochure.** Ni « super », ni « il suffit de », ni
  « comme vous pouvez le constater ». Si c'était si simple, le module ne servirait à rien.
- **« Il suffit de » est proscrit.** Cette tournure dit au stagiaire bloqué que son problème n'existe
  pas.
- **On assume les défauts du produit.** Quand un comportement de Kibana est déroutant, on le dit :
  « Cette requête ne renvoie rien, et Kibana ne vous dira pas pourquoi. Voici comment le voir. »
- **Vouvoiement**, y compris dans les consignes.

## 2. Vocabulaire

Le vocabulaire est celui de **l'interface en fr-FR de la version 9.5.3**, relevé dans le lab — jamais
traduit de tête. Les libellés cités sont vérifiés par `make verif-parcours`.

| À écrire | À ne pas écrire | Pourquoi |
|---|---|---|
| **Session Discover** | recherche enregistrée, saved search | Libellé de 9.5.3 en fr-FR, relevé dans le lab |
| **Tableaux de bord** | dashboards (en corps de texte) | Libellé de l'interface |
| **Section pliable** | section repliable, collapsible section | Libellé de l'interface |
| **data view** | index pattern | « index pattern » est l'ancien nom ; il n'apparaît plus |
| **champ keyword**, **champ text** | champ « mot-clé », champ « texte » | Ce sont des types Elasticsearch : on garde le nom technique |
| **plage de temps** | time range, période | Terme de l'interface |
| **panneau** | widget, tuile | Terme de l'interface |

Règle générale : **le libellé exact d'un élément d'interface se met entre guillemets français et se
cite tel qu'il s'affiche**, avec sa casse : « Ajouter un filtre ». Tout libellé cité doit exister dans
l'interface du lab — c'est vérifié automatiquement.

Quand le nom technique et le libellé diffèrent, on donne les deux la première fois, puis le libellé :
« la data view (affichée « Vue de données » dans le menu) ».

## 3. Anatomie d'un exercice

Tout exercice a **exactement** ces parties, dans cet ordre (SPEC §6.1) :

1. **Identifiant** — `M<n>-E<k>`, stable, cité dans la matrice du guide formateur.
2. **Objectif** — à quel objectif pédagogique du module il répond.
3. **Contexte SOC** — deux à quatre phrases. Une situation de salle, pas un prétexte : qui demande
   quoi, et pourquoi c'est urgent.
4. **Consignes** — numérotées. Leur précision dépend du niveau de guidage (§4).
5. **Indices à deux niveaux** — le premier oriente, le second montre presque. Le stagiaire les ouvre
   quand il veut ; le guide ne les impose pas.
6. **Champ de réponse** — ce qu'on attend : une adresse, un compte, un nombre, un choix. Le format est
   dit explicitement (« une adresse IPv4 », « un entier »).
7. **Solution commentée** — non pas la réponse, mais **le chemin** : pourquoi cette requête, ce que
   montre la visualisation, et **les erreurs typiques** à ce point précis.
8. **Lien vers la documentation** de la version.

### La règle qui prime sur toutes les autres

> **Un exercice dont la réponse est trouvable sans faire l'exercice est un défaut.**

Concrètement : aucune réponse attendue n'est écrite dans le parcours. Chaque exercice **renvoie** à une
réponse du manifeste (`data/manifest.json`), par scénario et par clé. Le guide n'embarque que des
empreintes SHA-256. Un exercice sans renvoi est refusé par `make verif-parcours`.

Corollaire : ne jamais écrire « vous devriez trouver environ 70 échecs ». Écrire « relevez le nombre
d'échecs » — le stagiaire le vérifie lui-même dans le guide.

## 4. Guidage dégressif

Chaque module progresse du plus guidé au plus autonome (SPEC §6.1). Le niveau est déclaré dans le
frontmatter, et il contraint la rédaction :

| Niveau | Ce que contiennent les consignes | Ce qu'elles ne contiennent pas |
|---|---|---|
| `demonstration` | Le geste complet, commenté, avec capture. Le stagiaire lit et reproduit. | — |
| `guide` | Toutes les étapes, dans l'ordre, avec les libellés exacts. | La réponse |
| `semi-guide` | L'objectif et les champs utiles. Pas la suite des clics. | Les étapes, la requête toute faite |
| `autonome` | La question d'enquête, rien d'autre. | Tout le reste |

Un module ne passe pas de `demonstration` à `autonome` sans passer par les deux niveaux du milieu. Le
capstone M4 est entièrement `autonome`.

## 5. Rappel actif

Chaque module s'ouvre sur **2 à 3 questions de rappel** du module précédent (SPEC §6.1). Ce sont des
questions de récupération, pas de reconnaissance : on demande de produire, pas de choisir. « Écrivez la
requête qui ne garde que les échecs d'authentification », pas « laquelle de ces trois requêtes… ».
M0 n'en a pas.

## 6. Une notion nouvelle par étape

Si une étape introduit deux notions, elle est coupée en deux. Le vocabulaire nouveau est défini à sa
première apparition et repris dans le glossaire. Les lignes du guide font **moins de 80 caractères**
(SPEC §7.3).

## 7. Les pièges

Les pièges de SPEC §6.3 sont **provoqués**, jamais décrits d'abord : le stagiaire fait la faute, voit
ce qui se passe, puis comprend. Chaque piège est relevé dans `docs/pieges-lab.json`, qui dit ce que la
version **fait réellement**. On n'écrit pas ce que le piège est censé produire, on écrit ce qu'il
produit.

Exemple de la différence, constaté en lab et à respecter :
- `destination.port : [1025 TO *]` → Kibana affiche « Impossible d’extraire les résultats de
  recherche ». C'est une erreur visible.
- `_exists_ : rule.name` → **zéro résultat, aucun message**. C'est le piège vraiment muet.

Écrire l'inverse serait faux, même si c'est ce qu'on attendait.

## 8. Conventions Markdown et YAML

Un module = un fichier `parcours/M<n>.md` = un frontmatter YAML + du Markdown.

### Frontmatter — schéma

```yaml
---
id: M1                          # M0 à M5
titre: Rechercher avec Discover
duree_minutes: 75
resume: Une phrase qui dit ce que le stagiaire saura faire à la fin.
objectifs:
  - id: M1-O1
    enonce: >-
      À l'issue du module, le stagiaire est capable de filtrer des événements
      avec KQL sur un champ keyword, un champ ip et un champ numérique.
rappel_actif:                   # absent en M0
  - question: Quelle plage de temps Discover applique-t-il par défaut ?
    reponse: Les 15 dernières minutes.
exercices:
  - id: M1-E1
    titre: Qui a échoué à se connecter cette nuit ?
    guidage: guide               # demonstration | guide | semi-guide | autonome
    duree_minutes: 10
    objectifs: [M1-O1]
    contexte: >-
      Le chef de salle vous signale ...
    consignes:
      - Ouvrez « Discover ».
      - ...
    indices:
      - Le champ qui porte le verdict s'appelle event.outcome.
      - Un échec d'authentification Windows porte le code 4625.
    format_de_reponse: une adresse IPv4
    reponse:                     # RENVOI au manifeste — jamais une valeur
      scenario: S1
      cle: source_ip
    requetes_kql:                # rejouées dans Discover par la vérification
      - kql: 'event.code : "4625"'
        attendu: non_vide        # non_vide | vide | manifeste:S1.nb_echecs
    libelles_ui:                 # vérifiés dans l'interface fr-FR du lab
      - Discover
      - Ajouter un filtre
    piege: exists-lucene-en-kql  # facultatif, identifiant de docs/pieges-lab.json
    solution: >-
      On part de ... parce que ...
    erreurs_typiques:
      - Oublier d'élargir la plage de temps : Discover affiche 15 minutes par défaut.
    doc: https://www.elastic.co/docs/explore-analyze/discover
---
```

### Règles YAML
- `reponse` ne contient **jamais** de valeur, seulement `scenario` + `cle`.
- `attendu` vaut `non_vide`, `vide`, ou `manifeste:<scenario>.<cle>` quand le nombre de résultats doit
  égaler une réponse du manifeste.
- Tout identifiant (`M1-E1`, `M1-O1`) est unique dans tout le parcours.
- Les blocs multilignes utilisent `>-` : pas de retour à la ligne parasite dans le guide.

### Règles Markdown
- Un seul titre de niveau 1 par fichier : celui du module.
- Les requêtes vont dans des blocs de code ` ```kql `, ` ```esql `, ` ```json ` — jamais en ligne.
- Les libellés d'interface entre guillemets français : « Ajouter un filtre ».
- Pas de tableau de plus de quatre colonnes : le guide se lit aussi sur un téléphone.
- Pas de capture décrite en mots (« comme sur l'image ») : la capture porte son propre texte
  alternatif, et le texte doit se suffire sans elle.

## 9. Typographie française

- Guillemets « français » avec **espace insécable** à l'intérieur.
- Espace insécable **avant** `: ; ! ?` et dans « 15 min », « 4 Go ».
- Les nombres de quatre chiffres et plus prennent une espace insécable fine comme séparateur de
  milliers : 384 592.
- Pas de majuscule à « data view », « keyword », « text ».
- Les noms de produits gardent leur casse : Kibana, Elasticsearch, Discover, Lens.

## 10. Ce qui est interdit

- Écrire une réponse attendue en clair dans le parcours.
- Citer un libellé d'interface sans l'avoir relevé dans le lab.
- Enseigner une capacité absente de `docs/capacites.md`, ou hors licence Basic sans encadré.
- Donner une requête qui n'a pas été rejouée dans Discover.
- Présenter un piège autrement qu'il ne se comporte dans `docs/pieges-lab.json`.
- Écrire une date absolue : les données sont en fenêtre glissante.
- Parler d'un fichier, d'un index ou d'une adresse qui ne viendrait pas du contexte fictif.
