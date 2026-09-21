# Guide du formateur

Kibana pour analystes SOC — Elastic Stack 9.5.3, licence Basic, interface fr-FR.
6 h de parcours, 35 exercices, 27 objectifs, plus 45 min d'évaluation.

---

## 1. La veille, ou le matin même

Trois commandes, dans cet ordre :

```bash
make lab-up      # démarre le lab et rejoue l'initialisation
make lab-reset   # réancre les données sur maintenant
make verif-lab   # 13 contrôles : licence, santé, locale, vue de solution, isolation
```

**`make lab-reset` n'est pas facultatif.** Les données sont en fenêtre
glissante : elles se terminent à l'instant du chargement. Sans réinitialisation,
la séance précédente vieillit, et deux scénarios perdent leur sens — celui de la
source muette « depuis deux heures », et celui du trou de collecte.

Comptez moins de cinq minutes. Vérifiez ensuite que Kibana répond sur
<http://localhost:5601> et que Discover montre des données sur sept jours.

À imprimer : la **fiche mémo** (`fiche-memo.pdf`, A4 recto verso) pour chaque
stagiaire, et le **quiz sans réponses** pour la fin de journée.

## 2. Déroulé minuté

| Heure | Durée | Séquence |
|---|---|---|
| 09 h 00 | 15 min | Accueil, tour de table, ce qu'on va faire et ce qu'on ne fera pas |
| 09 h 15 | 30 min | **M0 — Prise en main** |
| 09 h 45 | 77 min | **M1 — Rechercher avec Discover** |
| 11 h 02 | 13 min | Pause |
| 11 h 15 | 60 min | **M2 — Visualiser avec Lens** |
| 12 h 15 | 60 min | Déjeuner |
| 13 h 15 | 60 min | **M3 — Construire un tableau de bord** |
| 14 h 15 | 90 min | **M4 — Capstone SOC** |
| 15 h 45 | 15 min | Pause |
| 16 h 00 | 30 min | **M5 — Industrialiser** |
| 16 h 30 | 30 min | Quiz, puis correction commentée |
| 17 h 00 | 30 min | Épreuve pratique |
| 17 h 30 | 15 min | Débriefing, évaluation à chaud |

**Découpage en trois séances de 2 h** : M0 + M1 ; M2 + M3 ; M4 + M5 + évaluation.
Chaque séance commence alors par les questions de rappel actif du module, qui
sont faites pour ça.

**Si vous prenez du retard**, sacrifiez dans cet ordre : les exercices
semi-guidés de M2, puis M5-E3, puis un scénario de M4 parmi S2, S3 ou S5.
Ne sacrifiez jamais M4-E10 (la synthèse) ni le scénario S7 : ce sont les deux
seuls moments où l'on travaille le jugement plutôt que l'outil.

## 3. Pourquoi le parcours est construit ainsi

Ces choix ne sont pas des habitudes de rédaction ; ils portent la valeur du
parcours et méritent d'être expliqués aux stagiaires si la question vient.

**Exemple travaillé, puis guidage dégressif.** Chaque module commence par une
démonstration commentée, puis les consignes se retirent progressivement :
guidé, semi-guidé, autonome. Donner un exercice autonome d'emblée produit de
l'échec, pas de l'apprentissage ; ne donner que des exercices guidés produit des
stagiaires qui savent suivre une recette et rien d'autre. Le capstone M4 est
entièrement autonome : c'est là qu'on vérifie que le retrait a réussi.

**Rappel actif.** Chaque module s'ouvre sur deux ou trois questions sur le
module précédent, auxquelles on répond **sans revenir en arrière**. Se
remémorer fixe mieux que relire ; et une réponse qui ne vient pas signale un
point à reprendre avant qu'il ne bloque l'exercice suivant.

**Une question d'enquête par exercice.** La réponse se prouve, elle ne se
devine pas. Aucune réponse attendue ne figure dans le guide : il n'en contient
que des empreintes, et un contrôle automatique refuse tout exercice dont la
réponse serait trouvable sans le faire.

**Les pièges sont provoqués, jamais décrits d'abord.** Le stagiaire tape la
requête fausse, voit ce qui arrive, comprend. Un piège décrit à l'avance
s'oublie ; un piège vécu, non.

**Le leurre.** Un scénario sur sept est un faux positif, et il est vingt fois
plus bruyant que la vraie attaque. C'est le seul exercice du parcours où l'on
travaille le jugement. Laissez les stagiaires s'y tromper : la correction vaut
plus que l'évitement.

## 4. Matrice objectifs × exercices × questions

Engendrée et contrôlée par `formateur/matrice.py`, qui sort en erreur si un
objectif reste sans exercice ou sans question. Résultat courant :
**27 objectifs, 35 exercices, 15 questions, couverture 100 %.**

Le détail complet est dans `formateur/matrice.md`.

## 5. Erreurs fréquentes, et quoi dire

| Ce que vous verrez | Ce qui se passe | Ce que vous dites |
|---|---|---|
| « Il n'y a rien dans Kibana » | Plage de temps par défaut, trop courte | Ne donnez pas la réponse : « vérifie trois choses, dans l'ordre — data view, plage de temps, langage » |
| Une requête qui ne renvoie rien, sans message | Syntaxe Lucene tapée en KQL, typiquement `_exists_` | « Zéro résultat n'est pas une réponse, c'est une question. Qu'est-ce qui pourrait être faux avant les données ? » |
| `user.name : "SVC-Facturation"` → 0 | keyword, sensible à la casse | Faites-leur essayer la même chose sur `message` : le contraste fait tout |
| Un stagiaire devine des valeurs | Réflexe de développeur | Montrez le clic sur le champ dans la barre latérale. Une fois suffit |
| Un décompte distinct publié tel quel | Approximation au-delà de 3 000 | « Combien vaut ce chiffre, exactement ? » puis laissez-les chercher |
| Un tableau de bord à 20 panneaux | Envie de tout montrer | « Pour qui, et pour répondre à quelle question ? » |
| Conclusion hâtive sur S7 | Le volume impressionne | Ne corrigez pas tout de suite. Demandez : « qu'est-ce qui te permet de dire ça ? » |
| Un panneau vide au milieu d'un écran plein | Plage temporelle propre au panneau | Laissez-les chercher : c'est l'exercice M3-E4 |

## 6. Adapter le rythme

**Groupe débutant.** Faites M1-E5 et M1-E6 en collectif, au vidéoprojecteur.
Donnez d'emblée le second indice sur M2-E4. Sur M4, imposez l'ordre S1, S7, S6,
et laissez les autres scénarios en option : S1 met en confiance, S7 apprend le
doute, S6 apprend le raisonnement.

**Groupe confirmé.** Supprimez les démonstrations M1-E1 et M2-E1. Sur M4,
retirez les indices et donnez les sept scénarios d'un coup, en salle ouverte,
avec un seul chef de salle désigné qui centralise. Ajoutez la question : « quelle
requête feriez-vous tourner en continu pour que ceci vous saute aux yeux la
prochaine fois ? »

**Groupe mixte.** Appariez un confirmé et un débutant par poste sur M2 et M3,
et séparez-les sur M4 : le capstone doit se faire seul.

## 7. Questions de débriefing

À poser après M4, avant le quiz. Elles valent mieux qu'un récapitulatif.

1. Quel scénario vous a pris le plus de temps, et à quel moment précis avez-vous
   su que vous teniez la bonne piste ?
2. Qui a conclu à une attaque sur S7 avant de consulter la fiche de contexte ?
   Qu'est-ce qui vous y a poussé ?
3. Une source muette ne produit aucun groupe. Où ailleurs, dans votre travail,
   cette propriété pourrait-elle vous tromper ?
4. Lequel de vos panneaux serait encore juste dans six mois, et lequel ne le
   serait plus ?
5. Qu'est-ce que vous mettriez en place lundi, concrètement ?

## 8. Corrigé du quiz

Les explications complètes figurent dans le guide du stagiaire, qui les affiche
après validation. Les voici pour la correction en salle.

| Question | Réponse | Le point à faire passer |
|---|---|---|
| Q01 | `host.name` | Une machine change d'adresse, pas de nom |
| Q02 | data view, plage de temps, langage | Un écran vide n'est pas une absence de données |
| Q03 | Cliquer sur le champ | On ne devine jamais une valeur |
| Q04 | `destination.port >= 1025` | Les crochets sont du Lucene |
| Q05 | keyword sensible, text non | Le type du champ décide |
| Q06 | Zéro résultat, aucun message | Le piège muet, le plus coûteux |
| Q07 | Histogramme des dates, vérifier l'intervalle | L'intervalle change avec la plage |
| Q08 | Se méfier de « Autre » et des valeurs proches | Un classement désigne, il ne chiffre pas |
| Q09 | Approximatif au-delà de 3 000, sans avertissement | Le chiffre publié doit rester sous le seuil |
| Q10 | Formule et ligne de référence | La couleur renforce, elle ne remplace pas |
| Q11 | Plage temporelle propre au panneau | Elle l'emporte sur celle du tableau de bord |
| Q12 | Liste d'options sur un keyword | Le type du contrôle suit le type du champ |
| Q13 | La data view à identifiant fixe | Un objet défini par l'API n'a aucune référence |
| Q14 | Dernier événement vu par source | Une source muette ne produit aucun groupe |
| Q15 | Rien sans la fiche de contexte | Le volume ne dit rien du caractère malveillant |

## 9. Grilles d'évaluation

### La synthèse de cinq lignes (M4-E10)

| Critère | 0 | 1 | 2 |
|---|---|---|---|
| Verdict | Absent ou noyé | Présent mais imprécis | Net, dès la première ligne |
| Preuve | Aucune | Évoquée | Nommée et vérifiable |
| Faux positif | Confondu avec l'incident | Signalé sans preuve | Écarté, avec ce qui le prouve |
| Destinataire | Jargon d'analyste | Compréhensible avec effort | Lisible par un non-utilisateur de Kibana |
| Recommandation | Absente | Vague | Une action, un responsable |

Sur 10. Seuil d'acquisition : 6, **dont au moins 1 sur le critère « faux positif »**.

### L'épreuve pratique

| Critère | 0 | 1 | 2 |
|---|---|---|---|
| Collecte incomplète | Non traitée | Visible en cherchant | Saute aux yeux, la source est nommée |
| Attaque extérieure | Non traitée | Adresse OU compte | Adresse ET compte |
| Sortie anormale | Non traitée | Volume visible | Poste et destination identifiés |
| Titres en questions | Aucun | Quelques-uns | Tous |
| Réutilisable sans vous | Non enregistré | Enregistré, peu lisible | Enregistré, nommé, lisible seul |
| Synthèse | Absente | Descriptive | Utile à une décision |

Sur 12. Seuil d'acquisition : 8, **dont au moins 1 sur chacune des trois
premières lignes** — un tableau de bord qui ne répond qu'à deux questions sur
trois ne remplit pas la commande.

## 10. Dépannage du lab

| Symptôme | Cause | Remède |
|---|---|---|
| `make lab-up` s'arrête au pré-vol | Un prérequis manque | Le pré-vol affiche la commande exacte, y compris les `sudo` qu'il n'exécute jamais lui-même |
| Cluster `red`, shards non alloués | Disque sans place réelle | Libérez de l'espace. Le lab tolère un disque plein en pourcentage, pas un disque sans place |
| Kibana reste `unavailable` | Elasticsearch pas encore prêt | Attendez. `podman logs kibana-soc-lab-kibana` dit où il en est |
| Un stagiaire ne voit plus ses données | Il a changé de data view ou de Space | Vérifiez l'URL : elle contient `/s/formation/` |
| Un stagiaire a cassé son écran | C'est prévu | `make lab-reset` remet tout à neuf en moins de cinq minutes |
| Le lab ne répond pas sur réseau isolé | `bridge-nf-call-iptables` à 1 | `sudo sysctl -w net.bridge.bridge-nf-call-iptables=0` |
| Les données paraissent « vieilles » | `lab-reset` oublié | Relancez-le. C'est la cause la plus fréquente |

## 11. Ce que le kit ne contient pas, et pourquoi

L'application Elastic Security, le Machine Learning, Fleet, Canvas et Maps sont
hors périmètre. Un parcours d'une journée qui survole tout n'apprend rien.

Les rapports PDF et PNG, la planification d'envois et les drilldowns URL
n'existent pas en licence Basic. Le parcours le dit dans des encadrés plutôt que
de les passer sous silence : un stagiaire qui les cherchera en production doit
savoir pourquoi il ne les trouve pas.
