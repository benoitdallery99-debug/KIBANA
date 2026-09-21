# Note de conception

Kit de formation pratique à Kibana pour analystes SOC — Elastic Stack 9.5.3,
licence Basic, interface fr-FR.

---

## 1. Le besoin

Un SOC recrute. Chaque arrivant doit devenir utile sur Kibana en quelques jours :
savoir chercher dans les journaux, transformer une question d'enquête en
requête, et laisser derrière lui un tableau de bord que ses collègues
rouvriront. Les formations disponibles ont trois défauts récurrents.

D'abord, **elles enseignent l'outil, pas le métier**. On y apprend où cliquer,
sur un jeu de données de démonstration où tout se voit du premier coup. Le
lendemain, devant 400 000 événements dont 99 % sont bénins, l'analyste ne sait
pas par où commencer.

Ensuite, **elles ne sont pas reproductibles**. Elles s'appuient sur une instance
partagée, que le stagiaire précédent a laissée dans un état imprévisible, ou sur
un service en ligne inaccessible depuis un réseau cloisonné — ce qui est
précisément le cas d'un SOC.

Enfin, **elles vieillissent mal**. Les captures montrent une version d'il y a
deux ans ; les libellés cités n'existent plus ; une fonctionnalité enseignée
s'avère hors licence.

Le kit répond aux trois : un lab conteneurisé que le formateur réinitialise en
moins de cinq minutes, des données synthétiques qui ressemblent à une semaine
de production, et une chaîne de vérification qui refuse de livrer un guide dont
une seule affirmation ne serait plus vraie.

## 2. Les choix structurants, et ce qu'on a écarté

### Des données engendrées, plutôt qu'un extrait anonymisé

**Décision.** Toutes les données sont engendrées par un programme, à partir
d'une graine fixe. Aucune donnée réelle, même anonymisée.

*Alternative écartée* : partir d'un extrait de production anonymisé. C'est
tentant — le réalisme serait acquis — mais l'anonymisation d'un journal est un
problème non résolu : les adresses internes, les noms de machines et les
horaires suffisent souvent à ré-identifier. Et l'extrait ne serait pas
partageable entre clients.

*Conséquence gagnée, inattendue* : parce que les données sont engendrées, **les
réponses attendues sont connues du programme qui les fabrique**. Le kit n'a
jamais besoin qu'un humain écrive « la réponse est telle adresse ». Il lit la
réponse dans le manifeste du générateur, et la revérifie par une requête sur le
lab. Cette propriété est ce qui rend le reste possible.

### Une fenêtre glissante, plutôt que des dates figées

**Décision.** Les données se terminent à l'instant du chargement, sur sept jours.
Les réponses attendues sont donc des **valeurs** — une adresse, un compte, un
nombre — jamais des dates.

*Alternative écartée* : figer la période. Le jeu aurait vieilli : au bout d'un
mois, tous les exercices auraient demandé de remonter le sélecteur de temps
avant même de commencer, et le scénario « cette source s'est tue il y a deux
heures » n'aurait plus eu de sens.

*Coût assumé* : le formateur doit lancer `make lab-reset` avant chaque session.
C'est écrit en tête du README, et la commande est une seule ligne.

### Le lab décide, pas la documentation

**Décision.** Toute affirmation technique est cherchée dans la documentation
officielle, **puis éprouvée dans le lab**. En cas de divergence, le lab gagne, et
la divergence est consignée.

Cette règle a servi plus souvent que prévu. Trois exemples parmi ceux du journal :
- la documentation ne dit **nulle part** que les drilldowns URL exigent une
  licence Gold ; c'est le code de la version qui l'établit ;
- la SPEC elle-même annonçait qu'une syntaxe de plage Lucene tapée en KQL
  produisait un « échec silencieux ». En 9.5.3, elle affiche un message
  d'erreur. Le piège réellement muet est ailleurs — `_exists_:champ`, qui
  renvoie zéro résultat sans rien dire ;
- les sélecteurs du sélecteur de temps ont changé de nom entre versions, sans
  que rien ne le signale : un script qui les emploie ne lève aucune erreur, il
  ne trouve simplement plus l'élément.

Aucune de ces trois choses ne se serait vue sans exécution.

### Des tableaux de bord définis en code

**Décision.** Les deux tableaux de bord corrigés sont écrits en JSON et posés par
l'API Dashboards, GA depuis la 9.5 et disponible en licence Basic — vérifié sur
le lab.

*Alternative écartée* : les construire à la main dans l'interface et exporter le
ndjson. C'était la seule voie avant la 9.5, et elle reste nécessaire sur les
versions antérieures ; elle produit un JSON Lens illisible, impossible à relire
en revue et à maintenir.

*Nuance découverte à l'exécution* : l'API refuse qu'un panneau référence une
data view par son identifiant. Un tableau de bord défini en code est donc
autonome mais porte son motif d'index en dur, là où un tableau construit dans
l'interface référence sa data view. Les deux voies ont chacune leur usage — et
le module M5 les enseigne toutes les deux, avec cette différence pour matière.

## 3. Architecture

Deux mondes, qu'on ne mélange jamais.

**La chaîne de fabrication** tourne sur un poste connecté : elle engendre les
données, pilote un navigateur, construit le guide, produit les PDF et vérifie
tout. Elle a le droit de télécharger.

**Le livrable** est une archive de 1,5 Go qui ne télécharge jamais rien. Les
images de conteneurs y sont incluses, les dépendances Python en wheels, les
polices dans le guide. L'installation est éprouvée en pointant toutes les
variables de proxy vers un port mort : si quoi que ce soit tentait de sortir, il
échouerait au lieu de réussir en silence.

Le lab lui-même est un pod `podman kube play` à deux conteneurs, images
épinglées par empreinte et `imagePullPolicy: Never`. Il est prouvé fonctionnel
sur un réseau podman `--internal` — et il est prouvé qu'on ne peut pas en
sortir, avec un témoin sur le réseau ordinaire sans lequel le contrôle ne
démontrerait rien.

Un fichier, `kit.config.yaml`, porte les paramètres : version, locale, vue de
solution, graines, motifs d'index. Rien n'est écrit en dur ailleurs. Changer de
version consiste à modifier une ligne, relancer `make captures` et `make verif`.

## 4. Sécurité des données

Trois garanties, chacune contrôlée par un test.

**Aucune donnée réelle.** Adresses extérieures dans les plages de documentation
(RFC 5737), internes en RFC 1918, domaines en `.test` et `.example` (RFC 2606),
personnes inventées. Le contrôle ne porte pas sur l'intention du générateur mais
sur les **valeurs effectivement indexées** : il interroge le lab et refuse toute
adresse hors des plages réservées.

**Aucun secret commité.** Mots de passe et clés de chiffrement sont engendrés au
premier démarrage dans `.env`, en droits 600, gitignoré et absent de l'archive.
Un contrôle vérifie qu'il n'y voyage pas.

**Le lab est cloisonné, et il l'est pour une raison pédagogique.** Quatre
Spaces : celui de la formation, celui de l'équipe voisine — sans lequel la copie
d'un tableau de bord et l'import d'un export n'ont aucune cible —, celui des
corrigés, et celui de l'épreuve. Les deux derniers sont invisibles au compte du
stagiaire. Ce n'est pas de la sécurité pour la forme : un corrigé intitulé
« Tableau de bord corrigé du module M4 », visible dès la première connexion,
annule la journée. De même, le jeu de l'épreuve n'est lisible qu'entre
`make epreuve-ouvrir` et `make epreuve-fermer`. Des contrôles menés avec le
compte du stagiaire — et non avec un compte d'administration, qui ne prouverait
rien — le vérifient.

**Aucune réponse en clair.** Le guide n'embarque que des empreintes SHA-256 des
réponses normalisées : il peut dire « juste » ou « faux », jamais donner la
réponse. La règle a une exception, assumée et documentée : la fiche de contexte
publie le plan d'adressage, les serveurs critiques, les comptes de service et
l'adresse du scanner autorisé — comme en SOC réel, où l'analyste a ces éléments
sous les yeux. Une réponse s'y perd parmi ses semblables ; ailleurs, elle serait
une fuite, et un contrôle la refuse. Le manifeste de l'épreuve, lui, ne part
jamais avec le kit du stagiaire.

## 5. Parti pris pédagogique

**Guidage dégressif.** Chaque module va de la démonstration commentée à
l'exercice autonome, en passant par deux paliers. Le capstone est entièrement
autonome. Un contrôle vérifie que le guidage ne remonte jamais à l'intérieur
d'un module.

**Une question d'enquête par exercice.** La réponse se prouve — par une requête,
par une visualisation — elle ne se devine pas. La règle qui prime sur toutes les
autres est qu'**un exercice dont la réponse est trouvable sans faire l'exercice
est un défaut** ; elle est appliquée par un programme, pas par la bonne volonté
du rédacteur.

**Les pièges sont provoqués, pas décrits.** Le stagiaire tape la requête fausse
ou fait le geste fautif, voit ce qui se passe, comprend. Chacun des huit pièges
du parcours a été relevé dans le lab — six par une requête dans Discover, deux
par un geste dans l'interface — et le guide décrit ce qui arrive, pas ce qu'on
attendait. Un chiffre cité dans la leçon d'un piège est celui que la sonde vient
de mesurer, écrit par elle : « de 49 champs à 1 » n'est pas une estimation.

**Le leurre.** Un scénario sur sept est un faux positif : un scanner de
vulnérabilités autorisé produit, en une nuit, vingt fois plus d'échecs
d'authentification que la véritable attaque. Un analyste pressé conclura au plus
bruyant. L'élément qui tranche est dans la fiche de contexte, et personne ne le
lui signalera. C'est l'exercice le plus proche du métier de tout le parcours.

## 6. Stratégie de vérification

Sept suites, chacune lançable seule, toutes réunies par `make verif`. Le principe
qui les gouverne tient en une phrase : **un contrôle non exécuté est signalé
comme non exécuté, avec sa raison, jamais comme réussi**.

Ce que la vérification a réellement attrapé, et qu'une relecture humaine aurait
laissé passer :
- un réglage inventé qui empêchait Elasticsearch de démarrer ;
- un décompte de sources mesuré sur sept jours, qui restait au vert alors
  qu'une source était muette — un indicateur qui ne peut pas passer au rouge
  n'est pas un indicateur ;
- un scénario dont le domaine n'était pas distinguable des domaines internes ;
- un leurre qui ne dominait pas le décompte qu'il était censé dominer ;
- deux réponses identiques entre le jeu du parcours et celui de l'épreuve ;
- une suite de vérification qui détruisait le lab qu'elle vérifiait ;
- des sélecteurs d'interface périmés, qui n'échouaient pas mais ne trouvaient
  rien ;
- l'échappement HTML des gabarits, désactivé sans le dire : `select_autoescape`
  compare la dernière extension du fichier, et les gabarits s'appellent
  `.html.j2`. L'activer a d'ailleurs aussitôt cassé la validation des réponses,
  le script inliné partant lui aussi à l'échappement — et c'est la suite qui l'a
  dit, dans la minute ;
- une question de quiz qui énonçait, dans son texte, la réponse attendue d'un
  scénario.

Aucun de ces défauts n'était visible à la lecture. Tous ont été corrigés à la
cause, jamais en assouplissant le critère.

**Et ce que la vérification n'a PAS attrapé**, parce que la dire est plus utile
que de la vanter. Les deux relectures de P8 ont trouvé ce qu'aucune suite ne
regardait : des libellés d'interface cités de mémoire et non relevés à l'écran —
le contrôle existait, mais sa liste d'exceptions était si large qu'il ne
contrôlait plus rien ; des corrigés chargés dans le Space du stagiaire ; une
commande déclarée obligatoire dans le guide du formateur dont le script n'avait
jamais été écrit ; et trente exercices se partageant treize réponses. La leçon
tient en une ligne, et elle vaut au-delà de ce kit : **une suite verte ne prouve
que ce qu'elle regarde.** Chacun de ces défauts a donc reçu, en plus de sa
correction, le contrôle qui l'aurait vu.

## 7. Limites

**Le kit n'enseigne que ce qui existe en licence Basic.** Les rapports PDF et
PNG, la planification d'envois, les drilldowns URL n'y sont pas — mais leur
absence est dite dans un encadré quand elle surprendrait, plutôt que passée sous
silence.

**Il ne couvre pas l'application Elastic Security**, ni Machine Learning, ni
Fleet, ni Canvas, ni Maps. C'était un choix : un parcours d'une journée qui
survole tout n'apprend rien.

**Sur 90 capacités qualifiées, 64 n'ont pas été éprouvées dans le lab** ; elles
sont marquées comme telles, avec le test qui les trancherait. Elles ne
concernent aucune affirmation du parcours.

**Le kit a été fabriqué et vérifié sur une seule machine**, en 9.5.3. La
qualification sur la plateforme cible reste à faire par l'équipe qui
l'exploitera : c'est le premier point de la recette côté client.

## 8. Perspectives

La suite naturelle n'est pas d'ajouter des modules, mais de **fermer la boucle
avec la production**. Trois pistes, par ordre d'utilité :

1. **Un jeu de données propre à l'organisation.** Le générateur est paramétré
   par un contexte fictif ; remplacer ce contexte par le plan d'adressage réel
   du client — sans aucune donnée réelle, seulement la topologie — rendrait les
   exercices immédiatement transposables.
2. **Un parcours de niveau 2** sur la détection : règles d'alerte, seuils,
   détection de silence. Le module M5 en pose les fondations et s'arrête là où
   la licence Basic s'arrête.
3. **L'intégration au parcours d'intégration.** Le lab se réinitialise en moins
   de cinq minutes et l'évaluation est critériée : le kit peut servir de porte
   d'entrée à chaque arrivant, et la fiche d'évaluation à chaud alimenter sa
   propre correction.
