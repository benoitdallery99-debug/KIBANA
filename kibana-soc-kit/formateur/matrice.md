# Matrice objectifs × exercices × questions

Engendrée par `formateur/matrice.py`. Chaque objectif doit être couvert par
au moins un exercice **et** une question du quiz (SPEC §2).

- Objectifs : **27**
- Exercices : **35**
- Questions du quiz : **17**

| Objectif | Module | Exercices | Questions |
|---|---|---|---|
| `M0-O1` | M0 | M0-E1, M0-E3 | Q01, Q16 |
| `M0-O2` | M0 | M0-E2 | Q02 |
| `M0-O3` | M0 | M0-E2, M0-E3 | Q01 |
| `M1-O1` | M1 | M1-E1, M1-E3 | Q03, Q17 |
| `M1-O2` | M1 | M1-E2, M1-E4, M1-E5, M1-E6 | Q04 |
| `M1-O3` | M1 | M1-E2, M1-E3, M1-E6 | Q05 |
| `M1-O4` | M1 | M1-E5 | Q06 |
| `M1-O5` | M1 | M1-E4, M1-E5 | Q06 |
| `M2-O1` | M2 | M2-E1, M2-E2, M2-E3, M2-E5, M2-E6 | Q07 |
| `M2-O2` | M2 | M2-E2 | Q08 |
| `M2-O3` | M2 | M2-E3, M2-E6 | Q07 |
| `M2-O4` | M2 | M2-E4 | Q09 |
| `M2-O5` | M2 | M2-E5 | Q10 |
| `M3-O1` | M3 | M3-E1, M3-E4, M3-E6 | Q11 |
| `M3-O2` | M3 | M3-E2 | Q12 |
| `M3-O3` | M3 | M3-E3, M3-E6 | Q12 |
| `M3-O4` | M3 | M3-E4 | Q11 |
| `M3-O5` | M3 | M3-E1, M3-E5, M3-E6 | Q13 |
| `M4-O1` | M4 | M4-E1, M4-E7, M4-E8 | Q14 |
| `M4-O2` | M4 | M4-E2 | Q14 |
| `M4-O3` | M4 | M4-E3, M4-E4, M4-E5, M4-E6, M4-E7, M4-E8 | Q15 |
| `M4-O4` | M4 | M4-E9 | Q15 |
| `M4-O5` | M4 | M4-E10 | Q15 |
| `M5-O1` | M5 | M5-E1 | Q13 |
| `M5-O2` | M5 | M5-E2 | Q13 |
| `M5-O3` | M5 | M5-E3 | Q13 |
| `M5-O4` | M5 | M5-E4 | Q14 |

## Énoncés

- **M0-O1** — À l'issue du module, le stagiaire est capable de se connecter, de vérifier dans quel Space il travaille, de situer les données qu'il interroge — data view, data stream, index — et de lire le type d'un champ dans la barre latérale de Discover.
- **M0-O2** — À l'issue du module, le stagiaire est capable de régler la plage de temps de Discover et d'expliquer pourquoi un écran vide ne signifie pas une absence de données.
- **M0-O3** — À l'issue du module, le stagiaire est capable d'énumérer les sources disponibles dans le Space de formation, d'en donner le nombre, et de dire ce que les pourcentages de la barre latérale permettent de conclure — un écart massif, oui ; un classement, non.
- **M1-O1** — À l'issue du module, le stagiaire est capable de lire la barre latérale des champs et la table des documents, d'ajouter une colonne et d'ouvrir les documents alentour d'un événement.
- **M1-O2** — À l'issue du module, le stagiaire est capable d'écrire une requête KQL combinant égalité, and, or, not, joker, comparaison numérique et existence d'un champ.
- **M1-O3** — À l'issue du module, le stagiaire est capable d'expliquer pourquoi la casse compte sur un champ keyword et pas sur un champ text, et d'interroger un champ ip en notation CIDR.
- **M1-O4** — À l'issue du module, le stagiaire est capable de distinguer KQL, Lucene et ES|QL, et de reconnaître une syntaxe empruntée au mauvais langage.
- **M1-O5** — À l'issue du module, le stagiaire est capable de poser un filtre, de l'épingler, de l'inverser, de le désactiver, et d'enregistrer son travail dans une Session Discover.
- **M2-O1** — À l'issue du module, le stagiaire est capable de choisir la forme de visualisation qu'appelle une question — comparer, suivre une évolution, répartir, distribuer — et de la construire dans Lens.
- **M2-O2** — À l'issue du module, le stagiaire est capable de construire un classement avec « Valeurs les plus élevées », d'en régler le nombre de valeurs et le sens, et de dire pourquoi un classement peut être approché.
- **M2-O3** — À l'issue du module, le stagiaire est capable de construire un histogramme des dates, de choisir son intervalle et de reconnaître un intervalle partiel en bord de fenêtre.
- **M2-O4** — À l'issue du module, le stagiaire est capable de dire à quelle condition un décompte de valeurs distinctes est exact, et de refuser d'en publier un qui ne l'est pas.
- **M2-O5** — À l'issue du module, le stagiaire est capable d'écrire une formule, de poser une ligne de référence et de colorer une visualisation par valeur.
- **M3-O1** — À l'issue du module, le stagiaire est capable de composer une grille de panneaux, d'en régler le titre, la taille et la place, et de justifier cette place par une règle de conception.
- **M3-O2** — À l'issue du module, le stagiaire est capable d'ajouter des contrôles à un tableau de bord, de choisir leur type selon le type du champ, et de décider de leur portée par l'épinglage.
- **M3-O3** — À l'issue du module, le stagiaire est capable d'exploiter les interactions d'un tableau de bord — filtre au clic, passage vers Discover, exploration vers un autre tableau de bord.
- **M3-O4** — À l'issue du module, le stagiaire est capable de régler la plage de temps d'un panneau isolé et les paramètres du tableau de bord, et de dire ce que chacun change pour le lecteur.
- **M3-O5** — À l'issue du module, le stagiaire est capable d'enregistrer un tableau de bord avec ses balises, de le partager par lien, de le copier vers un autre Space, et de nommer ce que la licence Basic ne permet pas d'en exporter.
- **M4-O1** — À l'issue du module, le stagiaire est capable de construire un tableau de bord de santé de la collecte qui montre le volume de chaque source dans le temps, le dernier événement vu par source et les interruptions.
- **M4-O2** — À l'issue du module, le stagiaire est capable de construire une vue des alertes de la sonde qui montre leur gravité dans le temps, les signatures principales, les sources et les destinations les plus vues, et les dernières alertes reçues.
- **M4-O3** — À l'issue du module, le stagiaire est capable de conduire seul une enquête sur une piste d'authentification, de pare-feu, de résolution de noms ou de proxy, et de nommer l'élément qui la prouve.
- **M4-O4** — À l'issue du module, le stagiaire est capable de distinguer un incident avéré d'un faux positif en confrontant les journaux à la fiche de contexte de l'organisation.
- **M4-O5** — À l'issue du module, le stagiaire est capable de rédiger une synthèse de cinq lignes pour un chef de salle et de la noter avec une grille d'évaluation.
- **M5-O1** — À l'issue du module, le stagiaire est capable d'exporter un tableau de bord en ndjson, de dire ce que cet export contient et ce qu'il ne contient pas, et d'appliquer la règle de compatibilité entre versions.
- **M5-O2** — À l'issue du module, le stagiaire est capable de créer et de remplacer un tableau de bord par l'API Dashboards, de choisir entre ses deux routes, et de dire ce que ce format ne transporte pas.
- **M5-O3** — À l'issue du module, le stagiaire est capable de préparer le transport d'un écran avec une data view à identifiant fixe, et de dire ce qu'un import produit dans un Space où cet identifiant existe déjà.
- **M5-O4** — À l'issue du module, le stagiaire est capable de poser une règle d'alerte réalisable en licence Basic et de formuler une détection de silence qui se déclenche vraiment.

## Longueur des propositions du quiz

La bonne réponse est la proposition la plus longue dans **3** question(s) sur **17** (soit 18 %), pour un plafond de 25 % : Q01, Q02, Q10.
