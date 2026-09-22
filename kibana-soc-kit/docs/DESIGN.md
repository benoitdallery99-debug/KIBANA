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
| `--encre` | `#101720` | `#e6ebf2` | Texte courant |
| `--encre-douce` | `#44515f` | `#a7b3c1` | Texte secondaire, légendes |
| `--papier` | `#f3f5f8` | `#12161c` | Fond |
| `--action` | `#5b21b6` | `#c4a8ff` | **Réservé aux actions à faire dans Kibana** |
| `--alerte` | `#9c2a1a` | `#ff9b8a` | Pièges, erreurs, avertissements |

Plus quatre jetons d'appui, qui ne portent jamais de texte :

| Rôle | Clair | Sombre | Emploi |
|---|---|---|---|
| `--papier-appui` | `#e8edf2` | `#1b212a` | Fond des encadrés et des blocs de code |
| `--action-fond` | `#f1ebfd` | `#241a3a` | Fond des blocs « dans Kibana » |
| `--alerte-fond` | `#fbeeec` | `#34201c` | Fond des encadrés « piège » |
| `--filet` | `#7d8794` | `#616e7e` | Tout trait qui délimite un composant |

Le `--filet` valait `#c3ccd6` / `#2b333d` à la première rédaction. Mesuré, il tombait à **1,49:1** en
clair et **1,42:1** en sombre, sous les **3:1** que WCAG 1.4.11 exige d'un trait porteur
d'information — et les encadrés « piège » de ce guide ne se distinguent QUE par leur trait : sous ce
seuil, le piège cessait d'être signalé pour qui voit mal les contrastes. Les valeurs livrées donnent
3,34:1 et 3,49:1 sur `--papier`, 3,09:1 et 3,11:1 sur `--papier-appui`, le fond le moins favorable.

Contrastes mesurés sur le fond (calcul WCAG, script dans le journal) : encre 16,5:1 et 15,2:1 ;
encre douce 7,4:1 et 8,5:1 ; action 8,2:1 et 9,0:1 ; alerte 7,0:1 et 8,9:1. Tous au-dessus de 4,5:1,
dans les deux thèmes.

**Pourquoi le violet.** Elastic emploie le turquoise `#00BFB3`, le bleu `#0077CC`, le rose `#F04E98`
et le jaune `#FEC514`. Un accent bleu ou turquoise ferait du guide un faux Kibana. Le violet n'appartient
pas à cette palette : posé à côté de l'interface, il se lit immédiatement comme « ceci est le guide ».

### Rôles typographiques

| Rôle | Police | Taille | Graisse |
|---|---|---|---|
| Titre de module | Atkinson Hyperlegible Next | 2 rem | 700 |
| Titre de section | Atkinson Hyperlegible Next | 1,35 rem | 600 |
| Texte courant | Atkinson Hyperlegible Next | 1,0625 rem / 1,65 | 400 |
| Requête, champ, valeur | Atkinson Hyperlegible Mono | 0,95 rem | 400 |
| Numéro d'étape | Atkinson Hyperlegible Mono | 0,8 rem | 700 |

Deux familles, pas trois. Le monospace ne sert qu'à ce qui se tape ou se lit littéralement : une
requête, un nom de champ, une valeur. Cette règle est ce qui permet de repérer une requête sans la lire.

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
1. **Un seul marqueur pour les actions Kibana** : filet + carré plein + violet. Aucun autre élément du
   guide n'emploie cette combinaison. C'est la règle la plus importante du document.
2. **Une colonne, 68 caractères au plus.** Le guide se lit, il ne se scanne pas.
3. **Pas d'ombre, nulle part.** La hiérarchie vient du filet, de l'espace et de la graisse.
4. **La progression est une donnée.** Les pastilles du sommaire et la rangée S1→S7 disent où en est le
   stagiaire, et rien d'autre.
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
| Fond crème et accent terre cuite | **Évité.** Le papier est gris-bleu froid (`#f3f5f8`), l'accent violet. | **Tombe dedans.** `--papier` blanc et `--annotation` `#b3541e` est exactement une terre cuite. |
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
Une colonne, 68 caractères, interligne 1,65, Atkinson Hyperlegible Next — famille dessinée pour la
lisibilité, aux caractères ambigus volontairement différenciés (1 / l / I, 0 / O). Sur un guide qui
fait lire des adresses IP et des noms de champs, cette différenciation n'est pas un agrément : c'est
ce qui évite de taper `l0.10.13.23`.

La direction B, avec ses planches en vis-à-vis, impose une lecture en zigzag sur écran étroit.

### Distinction d'avec Kibana
Décisive, et c'est le critère qui tranche. Kibana est bleu-turquoise, dense, en grille, avec des
cartes et des ombres. La direction A est violette, en une colonne, sans carte ni ombre, avec un filet
de marge que Kibana n'a pas. Aucune confusion possible d'un coup d'œil.

La direction B, blanche et encadrée, ressemblerait davantage à un panneau Kibana sur fond clair.

### Accessibilité
Contrastes mesurés au-dessus de 4,5:1 dans les deux thèmes, pour les quatre couleurs de texte. Le
marqueur d'action ne repose pas sur la seule couleur : il combine un débordement de mise en page, un
carré plein et une étiquette textuelle « DANS KIBANA » — donc il survit au daltonisme, au mode
monochrome et à l'impression. Le filet de marge est décoratif et n'est jamais porteur d'information
seul.

### Ce que l'on garde de la direction B
La numérotation des figures et la légende sous la capture : c'est meilleur que de décrire une image
dans le corps du texte. Les captures annotées porteront donc des repères numérotés et une légende,
conformément à SPEC §7.2.

---

## Contrat que le code devra respecter

- Aucune `box-shadow`. Aucun `border-radius` supérieur à 4 px.
- `--action` n'apparaît que sur les blocs d'action Kibana et sur le focus. Nulle part ailleurs.
- Ligne de texte : `max-width: 68ch`.
- Focus visible : contour de 2 px en `--action`, décalé de 2 px, jamais supprimé.
- `prefers-reduced-motion` respecté : aucune transition au-delà de 0 ms si l'utilisateur le demande.
- Aucune animation décorative, nulle part.
- Thème : `prefers-color-scheme` par défaut, bascule manuelle qui l'emporte, choix mémorisé sous
  `try/catch`.
- Les deux thèmes se valent : le sombre n'est pas une inversion automatique, ses valeurs sont
  données ci-dessus.
- Zone `aria-live="polite"` pour les retours de validation de réponse.
- Tout doit rester lisible et utilisable en noir et blanc, et à l'impression.
