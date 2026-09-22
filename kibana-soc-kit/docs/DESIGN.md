# DESIGN — direction visuelle du guide

Écrit **avant** le code, comme l'impose SPEC §7.3 : palette nommée, rôles typographiques, maquettes,
principes, puis confrontation aux clichés, puis choix argumenté. Le code qui suivra applique ce
document ; s'il s'en écarte, c'est le code qu'on corrige.

## Le problème à résoudre

Un stagiaire lit le guide **sur un écran, à côté de Kibana**. Toutes les trente secondes, il passe de
l'un à l'autre. Trois exigences en découlent, et elles priment sur toute considération d'élégance :

1. **Il doit savoir en un coup d'œil s'il doit lire ou agir.** Un paragraphe explicatif et une action
   à faire dans Kibana ne doivent jamais se ressembler.
2. **Le guide ne doit pas ressembler à Kibana.** Deux interfaces bleu-turquoise côte à côte, et le
   stagiaire ne sait plus laquelle il regarde. C'est une exigence fonctionnelle, pas esthétique.
3. **Il doit savoir où il en est.** Le parcours est une séquence de six modules et de sept scénarios ;
   la progression est une information, pas une décoration.

---

## Direction A — « La main courante »

### Idée
La main courante d'une salle d'opérations : un registre continu, numéroté, où chaque entrée
s'inscrit dans l'ordre. Le guide n'imite pas un carnet ancien — il imite le **registre de service**
que le stagiaire tiendra demain.

L'élément signature est **un filet vertical continu dans la marge gauche**, sur lequel les numéros
d'étape s'accrochent comme des repères. Ce filet court d'un bout à l'autre du module : c'est la trace
de l'enquête, littéralement.

### Palette — 5 couleurs nommées

| Rôle | Clair | Sombre | Emploi |
|---|---|---|---|
| `--encre` | `#1b1a17` | `#eceaf2` | Texte courant |
| `--encre-douce` | `#55514a` | `#a9a6b2` | Texte secondaire, légendes |
| `--papier` | `#faf8f4` | `#16151a` | Fond |
| `--action` | `#5b21b6` | `#c4a8ff` | **Réservé aux actions à faire dans Kibana** |
| `--alerte` | `#9c2a1a` | `#ff9b8a` | Pièges, erreurs, avertissements |

Plus quatre jetons d'appui, qui ne portent jamais de texte :

| Rôle | Clair | Sombre | Emploi |
|---|---|---|---|
| `--papier-appui` | `#f1ede4` | `#201e25` | Fond des encadrés et des blocs de code |
| `--action-fond` | `#f1ebfd` | `#241a3a` | Fond des blocs « dans Kibana » |
| `--alerte-fond` | `#fbeeec` | `#34201c` | Fond des encadrés « piège » |
| `--filet` | `#7d8794` | `#6e7b8c` | Tout trait qui délimite un composant |

Le `--filet` valait `#c3ccd6` / `#2b333d` à la première rédaction. Mesuré, il tombait à **1,49:1** en
clair et **1,42:1** en sombre, sous les **3:1** que WCAG 1.4.11 exige d'un trait porteur
d'information — et les encadrés « piège » de ce guide ne se distinguent QUE par leur trait : sous ce
seuil, le piège cessait d'être signalé pour qui voit mal les contrastes.

Le rapport se mesure sur CE QUE LE TRAIT BORDE, et non sur le seul papier — une erreur que cette
page a faite : elle désignait `--papier-appui` comme « le fond le moins favorable » alors que
`--alerte-fond`, justement celui des encadrés « piège », l'est davantage. Le gris sombre `#616e7e`
tenait 3,49:1 sur `--papier` mais tombait à **2,95:1** sur `--alerte-fond`. Valeurs livrées, clair
puis sombre : 3,43 et 4,22 sur `--papier` ; 3,12 et 3,83 sur `--papier-appui` ; 3,22 et 3,56 sur
`--alerte-fond` ; 3,13 et 3,80 sur `--action-fond`. `make verif-guide` recalcule les seize.

Contrastes mesurés sur le fond (calcul WCAG, script dans le journal) : encre 16,41:1 et 15,24:1 ;
encre douce 7,44:1 et 7,60:1 ; action 8,47:1 et 8,99:1 ; alerte 7,17:1 et 8,91:1. Tous au-dessus de
4,5:1, dans les deux thèmes.

**Pourquoi le violet.** Elastic emploie le turquoise `#00BFB3`, le bleu `#0077CC`, le rose `#F04E98`
et le jaune `#FEC514`. Un accent bleu ou turquoise ferait du guide un faux Kibana. Le violet n'appartient
pas à cette palette : posé à côté de l'interface, il se lit immédiatement comme « ceci est le guide ».

**Pourquoi un papier chaud.** Le papier valait `#f3f5f8`, un gris-bleu froid, et l'encre `#101720`.
Le reproche d'un premier lecteur, mot pour mot : « du gris partout, un seul violet pâle, rien qui
accroche l'œil ». Le grief était juste, et il ne visait pas l'accent : il visait le fond. Un papier
légèrement chaud (`#faf8f4`) et une encre brun-noir (`#1b1a17`) suffisent à sortir le guide du
registre « application », qui est celui de Kibana — et la règle n° 2 s'en trouve mieux servie :
deux interfaces gris-bleu côte à côte, c'était précisément le risque de la première palette.

### Une teinte par module — 6 jetons de repérage

Le même reproche disait aussi autre chose : le guide ne montrait jamais **où on en est**. Le principe
n° 4 l'exigeait pourtant. Une teinte par module le rend visible sans ajouter un seul mot :

| Rôle | Clair | Sombre | Module |
|---|---|---|---|
| `--m0` | `#1a5a8a` | `#7fb8e6` | M0 — Prise en main |
| `--m1` | `#27684a` | `#71c99b` | M1 — Rechercher avec Discover |
| `--m2` | `#8a5510` | `#d9a441` | M2 — Visualiser avec Lens |
| `--m3` | `#39479b` | `#9fb0f5` | M3 — Construire un tableau de bord |
| `--m4` | `#8f2f6b` | `#e58ec0` | M4 — Capstone SOC |
| `--m5` | `#136b6e` | `#5cc7cb` | M5 — Industrialiser |

Trois contraintes ont fixé ces six valeurs, et pas le goût :

1. **Aucune n'est du violet.** `--action` est réservé aux actions à faire dans Kibana (principe n° 1) ;
   une teinte de module violette aurait posé la couleur de l'action sur un numéro d'exercice. Le M3
   valait `#5b3f9e` à la première écriture — c'était exactement cette faute, corrigée en indigo
   `#39479b`.
2. **Aucune n'est du rouge**, pour la même raison, avec `--alerte`.
3. **Toutes dépassent 4,5:1 sur les deux papiers**, parce qu'elles portent du texte et pas seulement
   des traits. Mesuré sur `--papier` : 6,89 · 6,25 · 5,84 · 7,77 · 7,10 · 5,90. Sur le papier sombre :
   8,56 · 9,11 · 8,07 · 8,65 · 7,75 · 9,07.

Il reste cinq familles chromatiques utilisables pour six modules : le bleu sert donc deux fois, en
acier pour M0 et en indigo pour M3. M0 et M3 ne se suivent jamais, et le sommaire écrit `M0` et `M3`
à côté du rail coloré — la couleur y confirme un repère, elle ne le porte pas seule.

La teinte n'apparaît qu'à quatre endroits : le rail du sommaire, le filet sous le titre de module, le
numéro d'exercice et son identifiant. **Jamais en aplat** — l'aplat plein reste le marqueur du bloc
d'action, et lui seul. Le numéro d'exercice a d'ailleurs commencé sa vie en pastille pleine, ce qui
violait le principe n° 1 : c'est un chiffre nu depuis.

### Rôles typographiques

| Rôle | Police | Taille | Graisse |
|---|---|---|---|
| Titre du guide | Source Serif 4 | clamp(2,2 – 3,4 rem) | 600 |
| Titre de module | Source Serif 4 | clamp(1,7 – 2,3 rem) | 600 |
| Titre de section du corps | Source Serif 4 | 1,55 rem | 600 |
| Titre d'exercice | Source Serif 4 | 1,32 rem | 600 |
| Numéro d'exercice | Source Serif 4 | 1,85 rem | 600 |
| Texte courant | Atkinson Hyperlegible Next | 1,0625 rem / 1,65 | 400 |
| Étiquette, méta, sommaire | Atkinson Hyperlegible Next | 0,76 – 0,93 rem | 400–600 |
| Requête, champ, valeur | Atkinson Hyperlegible Mono | 0,95 rem | 400 |
| Identifiant d'exercice | Atkinson Hyperlegible Mono | 0,76 rem | 700 |

Trois familles, et une seule règle pour les départager : **ce qui nomme** est en serif, **ce qui se
lit** est en sans-serif, **ce qui se tape** est en monospace. La titraille était en Atkinson comme le
reste, et les titres ne se distinguaient plus que par la taille — à tailles voisines, plus du tout.
Source Serif 4 est une police variable à axe optique (`opsz` 8–60) : le dessin d'un titre à 3,4 rem
n'est pas celui d'une étiquette à 0,82 rem, et `font-optical-sizing: auto` laisse la police s'en
charger. Elle est embarquée telle que distribuée (OFL, aucun sous-ensemble, aucune conversion),
comme l'impose CLAUDE.md — d'où les 1,2 Mo qu'elle ajoute au fichier autonome.

Le monospace ne sert qu'à ce qui se tape ou se lit littéralement : une requête, un nom de champ, une
valeur, un identifiant d'exercice. Cette règle est ce qui permet de repérer une requête sans la lire.

### Maquette — écran large

```
┌──────────────┬──────────────────────────────────────────────────────┐
│ SOMMAIRE     │  M1 — Rechercher avec Discover                       │
│              │                                                      │
│ M0 ●●●       │  Texte courant, une seule colonne, largeur limitée    │
│ M1 ●●○○○     │  à 68 caractères pour que l'œil revienne sans        │
│  · Champs    │  effort à la ligne suivante.                          │
│  · KQL       │                                                      │
│  · Filtres   │ ╻                                                    │
│ M2 ○○○       │ ┃ ▪ 3  DANS KIBANA                                   │
│ M3 ○○○       │ ┃    Ouvrez « Discover », puis réglez la plage       │
│ M4 ○○○○○○○   │ ┃    de temps sur les sept derniers jours.            │
│ M5 ○○○       │ ╹                                                    │
│              │                                                      │
│ ─────────    │  Le texte reprend ici, sans filet : on lit.          │
│ ENQUÊTE      │                                                      │
│ S1 ✓ S2 ✓    │  ┌─ requête ──────────────────────── [Copier] ─┐    │
│ S3 · S4 ·    │  │ event.code : "4625"                          │    │
│ S5 · S6 ·    │  └──────────────────────────────────────────────┘    │
│ S7 ·         │                                                      │
└──────────────┴──────────────────────────────────────────────────────┘
```

Le bloc d'action **déborde vers la gauche**, par-dessus le filet de marge. C'est ce débordement, et
non la couleur seule, qui le distingue : il reste lisible en noir et blanc, à l'impression.

### Maquette — téléphone

```
┌────────────────────────────┐
│ ☰  M1 · 2 / 5              │   barre compacte, position courante
├────────────────────────────┤
│ Texte courant, gouttière   │
│ de 16 px, une colonne.     │
│                            │
│ ╻ ▪ 3  DANS KIBANA         │   le filet passe à gauche du bloc,
│ ┃  Ouvrez « Discover »…    │   le débordement disparaît faute
│ ╹                          │   de marge : la couleur et le carré
│                            │   portent seuls la distinction
│ ┌ requête ───── [Copier] ┐ │
│ │ event.code : "4625"    │ │
│ └────────────────────────┘ │
└────────────────────────────┘
```

### Principes
1. **Un seul marqueur pour les actions Kibana** : filet + aplat + violet. Aucun autre élément du
   guide n'emploie cette combinaison — ni les six teintes de module, qui ne sont jamais posées en
   aplat, ni le numéro d'exercice, qui est un chiffre nu. C'est la règle la plus importante du
   document, et celle qui a coûté le plus de reprises.
2. **Une colonne, 68 caractères au plus.** Le guide se lit, il ne se scanne pas.
3. **Pas d'ombre, nulle part.** La hiérarchie vient du filet, de l'espace et de la graisse.
4. **La progression est une donnée.** Le compteur du sommaire (`0/5`), la rangée S1→S7 et la teinte
   du module courant disent où en est le stagiaire, et rien d'autre.
5. **Tout fonctionne en noir et blanc**, parce que la fiche mémo s'imprime.

---

## Direction B — « La planche d'expertise »

### Idée
La planche de laboratoire : chaque capture est une **pièce numérotée**, avec sa légende sous elle,
comme une planche scientifique. Le guide est une suite de planches ; le texte les relie.

### Palette

| Rôle | Clair | Sombre |
|---|---|---|
| `--encre` | `#16181a` | `#eceff1` |
| `--papier` | `#ffffff` | `#0d0f11` |
| `--trait` | `#9aa3ab` | `#3a4249` |
| `--annotation` | `#b3541e` | `#ff9d5c` |
| `--mesure` | `#1f5c4a` | `#7fd3b8` |

### Maquette

```
┌─────────────────────────────────────────────────────────┐
│  PLANCHE 4                                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │  [capture annotée, repères ① ② ③]                 │  │
│  └───────────────────────────────────────────────────┘  │
│  ① barre de requête  ② sélecteur de temps  ③ champs     │
│                                                          │
│  Le texte commente la planche, en vis-à-vis.            │
└─────────────────────────────────────────────────────────┘
```

### Principes
Grille stricte, filets capillaires, légendes numérotées sous chaque planche, beaucoup de blanc, aucune
couleur d'accent hors annotation.

---

## Confrontation aux clichés (SPEC §7.3)

| Cliché à éviter | Direction A | Direction B |
|---|---|---|
| Fond crème et accent terre cuite | **Évité, et c'est plus serré qu'à la première écriture.** Le papier a été réchauffé de `#f3f5f8` à `#faf8f4` — mais `#faf8f4` est un blanc cassé à 3 % de saturation, pas un crème (un crème, c'est `#f5efdc` et 30 %), et l'accent reste violet. Le cliché nomme un COUPLE ; il n'est pas formé. | **Tombe dedans.** `--papier` blanc et `--annotation` `#b3541e` est exactement une terre cuite. |
| Noir et vert acide | Évité : pas de vert. | Évité, mais `--mesure` vert-sapin frôle le registre. |
| Cartes arrondies identiques à ombre grise | **Évité par principe n° 3** : aucune ombre, aucune carte. Le bloc d'action est un débordement, pas une carte. | Évité : la planche est encadrée d'un filet, pas d'une ombre. |
| Étiquettes en capitales espacées au-dessus des titres | Évité. Une seule étiquette existe, « DANS KIBANA », et elle n'est pas décorative : elle nomme une action. | **Tombe dedans** : « PLANCHE 4 » en capitales au-dessus de chaque bloc est précisément ce motif. |
| Un seul mot mis en exergue par titre | Évité : les titres sont des phrases ou des questions. | Évité. |
| Flèches « → » accolées aux boutons | Évité : les commandes du guide sont des verbes (« Copier », « Vérifier ma réponse »). | Évité. |

La direction B tombe dans deux clichés sur six, et l'un des deux — la terre cuite — est nommément cité
par la SPEC. Ce n'est pas rédhibitoire en soi : il suffirait de changer l'accent. Mais cela révèle
que sa palette n'était pas motivée par le sujet.

---

## Choix : direction A, « La main courante »

### Ancrage dans le sujet
La main courante est un objet que le stagiaire connaît : c'est ce qu'il tiendra en salle. La planche
d'expertise renvoie au laboratoire, à l'analyse a posteriori — pas au travail de permanence. Entre
deux métaphores défendables, on prend celle du métier visé.

### Lisibilité
Une colonne, 68 caractères, interligne 1,65, Atkinson Hyperlegible Next pour le corps — famille dessinée pour la
lisibilité, aux caractères ambigus volontairement différenciés (1 / l / I, 0 / O). Sur un guide qui
fait lire des adresses IP et des noms de champs, cette différenciation n'est pas un agrément : c'est
ce qui évite de taper `l0.10.13.23`. La titraille, elle, est en serif : elle ne se lit pas en
continu, elle se repère, et un changement de famille se repère mieux qu'un changement de corps.

La direction B, avec ses planches en vis-à-vis, impose une lecture en zigzag sur écran étroit.

### Distinction d'avec Kibana
Décisive, et c'est le critère qui tranche. Kibana est bleu-turquoise, dense, en grille, avec des
cartes et des ombres. La direction A est violette sur papier chaud, en une colonne, sans carte ni
ombre, avec une titraille en serif et un filet de marge que Kibana n'a pas. Aucune confusion possible
d'un coup d'œil — et le passage du gris-bleu au papier chaud a écarté le seul point de ressemblance
qui restait.

La direction B, blanche et encadrée, ressemblerait davantage à un panneau Kibana sur fond clair.

### Accessibilité
Contrastes mesurés au-dessus de 4,5:1 dans les deux thèmes, pour les quatre couleurs de texte. Le
marqueur d'action ne repose pas sur la seule couleur : il combine un débordement de mise en page, un
carré plein et une étiquette textuelle « DANS KIBANA » — donc il survit au daltonisme, au mode
monochrome et à l'impression. Le filet de marge est décoratif et n'est jamais porteur d'information
seul. Les six teintes de module sont un second niveau de repérage, jamais le seul : le sommaire
écrit `M0` … `M5` à côté du rail coloré, et le numéro d'exercice est un chiffre avant d'être une
couleur.

### Ce que l'on garde de la direction B
La numérotation des figures et la légende sous la capture : c'est meilleur que de décrire une image
dans le corps du texte. Les captures annotées porteront donc des repères numérotés et une légende,
conformément à SPEC §7.2.

---

## Contrat que le code devra respecter

- Aucun `border-radius` supérieur à 4 px.
- **Une seule `box-shadow` dans tout le guide**, et elle est fonctionnelle : l'infobulle du
  glossaire, qui flotte au-dessus du texte courant et doit se lire comme détachée de lui. Partout
  ailleurs, la profondeur se dit par un trait. `make verif-guide` recompte les ombres et refuse la
  deuxième.
- `--action` porte tout ce qui SE FAIT ou SE SUIT : les blocs d'action Kibana, le focus, les liens,
  la position courante du sommaire, le repère d'une réponse juste, le surlignage de recherche.
  La première rédaction disait « les blocs d'action et le focus, nulle part ailleurs », et le code
  ne l'a jamais respecté — un lien sans couleur d'accent n'est pas un lien. Ce qui reste interdit,
  c'est de l'employer en ORNEMENT : un fond, un liseré ou un titre qui ne se clique pas et ne
  signale aucune position.
- Ligne de texte : `max-width: 68ch`. PIÈGE mesuré : `ch` se résout sur la taille de police de
  l'élément, si bien qu'un titre à 2 rem posé dans un conteneur non borné s'autorisait 1 266 px
  pour 1 104 px de place, filet compris. Là où la taille varie, c'est `--colonne-fixe` (46,5 rem)
  qui borne.
- **Trois familles, trois rôles** : serif pour ce qui nomme, sans-serif pour ce qui se lit, monospace
  pour ce qui se tape. Aucune exception.
- **La teinte du module n'est jamais un aplat** : rail, filet, chiffre, identifiant — rien d'autre.
- Focus visible : contour de 2 px en `--action`, décalé de 2 px, jamais supprimé.
- `prefers-reduced-motion` respecté : aucune transition au-delà de 0 ms si l'utilisateur le demande.
- Aucune animation décorative, nulle part.
- Thème : `prefers-color-scheme` par défaut, bascule manuelle qui l'emporte, choix mémorisé sous
  `try/catch`.
- Les deux thèmes se valent : le sombre n'est pas une inversion automatique, ses valeurs sont
  données ci-dessus.
- Zone `aria-live="polite"` pour les retours de validation de réponse.
- Tout doit rester lisible et utilisable en noir et blanc, et à l'impression.
