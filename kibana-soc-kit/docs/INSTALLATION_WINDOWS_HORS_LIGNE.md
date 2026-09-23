# Installer le kit Kibana sur un PC Windows hors ligne

Guide pas à pas. Chaque commande est à taper **telle quelle**, **une à la
fois**, puis Entrée. Après chaque étape importante, un encadré **Attendu** dit
ce que l'écran doit montrer : si ce n'est pas le cas, arrêtez-vous et voyez
« Quand ça coince », en fin de document.

---

## 0. En bref

Le kit fait tourner **Kibana et Elasticsearch 9.5.3** dans une **Ubuntu logée
dans Windows** (WSL2). Windows sert seulement à l'héberger, et à ouvrir Kibana
dans Edge ou Chrome. Aucune connexion Internet n'est nécessaire sur le PC de
formation : tout est sur la clé.

| Durée indicative | |
|---|---|
| Préparer la clé (partie A, poste connecté) | 10 minutes |
| Installer WSL, s'il manque (partie B2) | 10 minutes et un redémarrage |
| Installer le kit (parties B3 à B8) | 10 minutes |
| Vérifier (partie B9) | 1 minute |

Deux comptes de connexion à Kibana :

| Identifiant | Pour qui | Ce qu'il voit |
|---|---|---|
| `stagiaire` | les stagiaires | les Spaces « formation » et « reseau » |
| `admin` | le formateur | les quatre Spaces, **corrigés compris** |

Leurs mots de passe sont dans le fichier `comptes.env` de la clé. Ils ne
figurent pas dans le dépôt du kit, qui est public.

---

## 1. Ce qu'il y a sur la clé

Le dossier **`kit-media`**, environ **2,3 Go** :

| Fichier | Rôle |
|---|---|
| `LISEZMOI.html` | ce guide, à ouvrir dans le navigateur (double-clic) |
| `LISEZMOI.md` | le même guide, en texte |
| `VERSION.txt` | versions exactes de tout ce que contient la clé |
| `comptes.env` | mots de passe des comptes `stagiaire` et `admin` |
| `ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz` (+ `.sha256`) | Ubuntu 24.04 officielle pour WSL, 340 Mo, empreinte publiée par Canonical |
| `wsl.2.6.1.0.x64.msi` (+ `.sha256`) | l'installateur de WSL, 246 Mo — pour un PC qui ne l'a pas encore |
| `debs/` | 47 paquets système (podman, iptables, make, Python…) et leur index |
| `installer-prerequis-horsligne.sh` | installe ces paquets sans réseau, et crée l'utilisateur du lab |
| `kit-formation-kibana-9.5.3-<date>.tar.gz` (+ `.sha256`) | le kit : images Elasticsearch et Kibana, Python, guide, PDF — 1,6 Go |
| `MEDIA.SHA256` | l'empreinte de chaque fichier de la clé |

---

## 2. Ce qu'il faut sur le PC de formation

| | Minimum | Pourquoi |
|---|---|---|
| Windows | 10 (build 19041 ou plus) ou 11 | WSL2 |
| Processeur | **x86_64** (Intel ou AMD) | les images du lab sont `amd64` : un PC ARM ne convient pas |
| Mémoire | 16 Go | le lab en prend 6 dans WSL2 |
| Disque `C:` | 20 Go libres | Ubuntu, images, données |
| Virtualisation | active dans le BIOS | WSL2 ; activée sur la plupart des PC récents |
| Droits | administrateur **seulement si WSL manque** | partie B2 |
| Docker Desktop | **fermé**, s'il est installé | il partage le noyau de WSL2 |

---

## 3. Deux fenêtres, deux invites — ne pas les confondre

Tout au long du guide, deux sortes de commandes :

- **Commandes Windows** : dans l'**invite de commandes** (touche Windows,
  tapez `cmd`, Entrée). L'invite ressemble à `C:\Users\vous>`.
- **Commandes Ubuntu** : dans la fenêtre Ubuntu, ouverte par `wsl -d kibana-lab`.
  L'invite se termine par `#` (root) ou par `$` (utilisateur `formation`).

Une commande Windows tapée dans Ubuntu répond `command not found`, et
inversement. Chaque bloc ci-dessous dit dans quelle fenêtre on est.

---

## Partie A — Préparer la clé, sur un poste connecté

À faire **une fois**, sur un PC Windows connecté où le kit tourne déjà (voir
`INSTALLATION_WINDOWS_UBUNTU.md`).

**Fenêtre Ubuntu** (votre Ubuntu habituelle) :

```
cd ~/kit/kibana-soc-kit
```

```
make lab-images
```

> **Attendu** : deux lignes `digest épinglé tiré et étiqueté 9.5.3`.

```
make guide
```

```
bash outils/preparer-media-windows.sh
```

Le script demande deux mots de passe, qu'il écrit dans `comptes.env` :

```
  Mot de passe de « stagiaire » (6 caractères au moins, Entrée : plus tard) :
  Retapez-le :
  Mot de passe de « admin » (6 caractères au moins, Entrée : plus tard) :
  Retapez-le :
```

Rien ne s'affiche pendant la frappe : c'est normal. **Six caractères au
moins** : Elasticsearch refuse en dessous (mesuré — `cdri` est refusé,
`cdricdri` accepté).

> **Attendu**, après environ 10 minutes :
> `Support prêt : /mnt/c/kit-media (2.3G)`, suivi du contenu de `VERSION.txt`.

**Copiez ensuite le dossier `C:\kit-media` sur la clé USB, en entier.**

---

## Partie B — Installer, sur le PC hors ligne

### B1. Copier la clé sur le disque

Branchez la clé, et copiez son dossier `kit-media` **à la racine de `C:`**,
pour obtenir `C:\kit-media`. Toutes les commandes supposent cet emplacement.

Ouvrez `C:\kit-media\LISEZMOI.html` dans le navigateur : c'est ce guide, plus
commode à lire qu'à imprimer.

### B2. WSL est-il installé ?

**Invite de commandes Windows** :

```
wsl --status
```

- S'il répond par des informations (version par défaut, etc.) : **WSL est
  présent**, passez directement à **B3**.
- S'il dit que WSL n'est pas installé : faites **B2 bis**.

### B2 bis. Installer WSL sans Internet

> **Non éprouvé sur un poste réel** : le PC où ce guide a été testé avait déjà
> WSL. Les commandes ci-dessous sont celles que documente Microsoft ; en cas
> d'écart, notez le message exact.

Ouvrez une invite de commandes **en administrateur** : touche Windows, tapez
`cmd`, clic droit sur « Invite de commandes », **Exécuter en tant
qu'administrateur**.

Activez les deux fonctionnalités Windows :

```
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

```
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

> **Attendu**, pour chacune : `L'opération a réussi.`

Vérifiez que l'installateur de WSL est bien signé par Microsoft :

```
powershell -Command "(Get-AuthenticodeSignature C:\kit-media\wsl.2.6.1.0.x64.msi).Status"
```

> **Attendu** : `Valid`.

Redémarrez le PC :

```
shutdown /r /t 0
```

Après le redémarrage, invite de commandes **en administrateur** à nouveau :

```
msiexec /i C:\kit-media\wsl.2.6.1.0.x64.msi
```

Suivez l'assistant jusqu'au bout. Puis vérifiez :

```
wsl --version
```

> **Attendu** : `Version WSL : 2.6.1.0`, suivi d'autres versions.

Si `wsl --status` signale ensuite que la virtualisation est désactivée : il
faut l'activer dans le BIOS du PC (Intel VT-x ou AMD-V), ce qui relève du
service informatique.

### B3. Créer l'Ubuntu du lab

**Invite de commandes Windows** (pas besoin d'administrateur) :

```
mkdir C:\wsl\kibana-lab
```

```
wsl --import kibana-lab C:\wsl\kibana-lab C:\kit-media\ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz --version 2
```

> **Attendu** : `L'opération a réussi.` (environ 30 secondes)
>
> Sans le `mkdir`, l'import échoue sur `Wsl/ERROR_PATH_NOT_FOUND` — mesuré
> sur un vrai PC.

```
wsl -d kibana-lab
```

> **Attendu** : une invite qui se termine par **`#`**. Vous êtes dans Ubuntu,
> en root, pour la seule étape suivante.

### B4. Contrôler la clé et installer les prérequis

**Fenêtre Ubuntu, en root (`#`)** :

```
cd /mnt/c/kit-media
```

```
sha256sum -c --quiet MEDIA.SHA256 && echo "support intègre"
```

> **Attendu** : `support intègre`. Toute autre sortie : **arrêtez**, la copie
> de la clé est abîmée ; recopiez-la.

```
bash installer-prerequis-horsligne.sh
```

Le script installe 47 paquets, puis crée l'utilisateur **`formation`**, sous
lequel le lab tournera. Il demande son mot de passe Linux, deux fois — il ne
sert qu'à la commande `sudo`. Choisissez-en un simple et notez-le (par exemple
`formation`). Des questions « Full Name », « Room Number »… peuvent
apparaître : appuyez sur Entrée à chacune, puis `Y`.

> **Attendu**, en fin de script :
> ```
>   paquets non configurés : 0
> podman version 4.9.3
> GNU Make 4.3
> Python 3.12.3
> venv disponible
> == Utilisateur « formation » ==
>   utilisateur par défaut de la distribution : formation
> ```

**Pourquoi un utilisateur et pas root** : mesuré sur un vrai PC Windows, en
root, podman publie les ports du lab d'une manière qui, sous WSL, rend
Elasticsearch injoignable ; sous un utilisateur ordinaire, tout fonctionne.

Quittez Ubuntu :

```
exit
```

**Invite de commandes Windows** — redémarrez la distribution pour qu'elle
prenne l'utilisateur `formation` :

```
wsl --terminate kibana-lab
```

```
wsl -d kibana-lab
```

> **Attendu** : une invite en **`formation@…:…$`**. À partir d'ici, tout se
> fait sous cet utilisateur.

### B5. Installer le kit

**Fenêtre Ubuntu, en `formation` (`$`)** :

```
cd ~
```

```
mkdir -p ~/kit
```

```
tar xzf /mnt/c/kit-media/kit-formation-kibana-*.tar.gz -C ~/kit
```

Une minute environ, sans affichage.

```
cd ~/kit/kit-formation-kibana-*
```

```
./installer.sh
```

> **Attendu** (environ 2 minutes) :
> ```
> == Vérification des empreintes ==
>   empreintes conformes
> == Chargement des images de conteneurs ==
>   …
>   mirror.gcr.io/library/elasticsearch:9.5.3
>   mirror.gcr.io/library/kibana:9.5.3
> == Environnement Python ==
>   dépendances installées depuis wheels/
> ```
>
> L'avertissement `"/" is not a shared mount` est sans effet.

### B6. Fixer les mots de passe

```
make mots-de-passe DEPUIS=/mnt/c/kit-media/comptes.env
```

> **Attendu** :
> ```
>   [OK]  « stagiaire » (stagiaire) : lab arrêté : sera appliqué au prochain « make lab-up »
>   [OK]  « admin » (formateur) : lab arrêté : sera appliqué au prochain « make lab-up »
> Mots de passe enregistrés dans .env (droits 600).
> ```

S'il n'y a pas de `comptes.env` sur la clé, tapez simplement
`make mots-de-passe` : la commande demande les deux mots de passe.

### B7. Démarrer le lab

```
make lab-up
```

> **Attendu** (environ 1 minute) : le pré-vol, tout en `[OK]` ; puis
> ```
> [rendre_pod] digest épinglé introuvable dans le magasin local … Réancrage sur le magasin.
> …
>   Elasticsearch prêt (santé « green ») en 26s.
>   Kibana disponible en 6s.
> …
>   [OK]    Compte « admin » (rôle « formateur »)
>   [OK]    Compte « stagiaire » (rôle « stagiaire »)
> …
> Lab prêt.  Kibana : http://localhost:5601
> ```
>
> Le message « Réancrage » est **normal et prévu** : les images chargées
> depuis la clé ne portent pas la même empreinte que celles du registre, et
> le kit s'y adapte.

### B8. Charger les données

```
make data
```

```
make data-epreuve
```

```
make corriges
```

> **Attendu** : environ 380 000 documents par jeu ; pour `make data`, la
> dernière ligne `dist/guide.html — 4.43 Mo, 6 modules, 35 exercices, 17
> questions de quiz` ; pour `make corriges`, `[OK] Santé de la collecte` et
> `[OK] Vue IDS`.

### B9. Vérifier

```
sudo sysctl -w net.bridge.bridge-nf-call-iptables=0
```

(mot de passe : celui de l'utilisateur `formation`, choisi en B4)

```
make verif-lab verif-donnees
```

> **Attendu** — mesuré sur le PC d'essai, hors ligne :
> ```
> ======= 19 passed, 1 skipped =======
> ======= 14 passed =======
> ```
> Aucun `FAILED`. Le contrôle `test_reseau_interne_interdit_toute_sortie`
> sort en **SKIPPED**, et c'est la preuve que le PC est bien hors ligne : il
> compare le réseau isolé du lab à un témoin qui doit pouvoir sortir, et sans
> Internet, rien ne sort. Avec moins de 12 Go de mémoire dans WSL,
> `test_lab_fonctionne_sur_reseau_interne` sort aussi en SKIPPED : c'est
> attendu.

### B10. Ouvrir Kibana et le guide

Dans **Edge ou Chrome**, côté Windows : **http://localhost:5601**

| Pour | Identifiant | Mot de passe |
|---|---|---|
| un stagiaire | `stagiaire` | celui de `comptes.env` |
| le formateur | `admin` | celui de `comptes.env` |

Après connexion, choisissez le Space **formation**. Les stagiaires ne doivent
pas recevoir le mot de passe `admin` : ce compte voit les corrigés.

Pour lire les mots de passe sans ouvrir le fichier, **fenêtre Ubuntu** :

```
cat /mnt/c/kit-media/comptes.env
```

Le guide interactif du stagiaire :

```
cp dist/guide.html /mnt/c/kit-media/
```

puis, dans Windows, double-cliquez `C:\kit-media\guide.html`. Il s'ouvre dans
le navigateur, sans réseau.

---

## Partie C — Au quotidien

| Pour | Où | Commande |
|---|---|---|
| Ouvrir Ubuntu | invite Windows | `wsl -d kibana-lab` |
| Aller dans le kit | Ubuntu | `cd ~/kit/kit-formation-kibana-*` |
| Démarrer le lab (après un redémarrage du PC) | Ubuntu, dans le kit | `make lab-up` |
| Arrêter le lab | Ubuntu, dans le kit | `make lab-down` (les données sont conservées) |
| Remettre à neuf avant une séance | Ubuntu, dans le kit | `make lab-reset` (2 minutes ; le guide `dist/guide.html` est reconstruit — recopiez-le) |
| Ouvrir l'épreuve pratique aux stagiaires | Ubuntu, dans le kit | `make epreuve-ouvrir` |
| La refermer | Ubuntu, dans le kit | `make epreuve-fermer` |
| Changer un mot de passe | Ubuntu, dans le kit | `make mots-de-passe` (il demande, sans afficher) |

**Gardez la fenêtre Ubuntu ouverte pendant toute la séance.** Quand la
dernière fenêtre d'une distribution WSL se ferme, Windows peut l'arrêter au
bout de quelques instants — et le lab avec elle. Si Kibana ne répond plus :
`wsl -d kibana-lab`, `cd ~/kit/kit-formation-kibana-*`, `make lab-up`.

---

## Partie D — Tout désinstaller

**Invite de commandes Windows** :

```
wsl --unregister kibana-lab
```

```
rmdir /s /q C:\wsl\kibana-lab
```

Tout ce que contenait l'Ubuntu du lab disparaît : kit, images, données. Le
dossier `C:\kit-media` reste ; supprimez-le si vous n'en avez plus besoin.

---

## Partie E — Répéter la procédure sur un PC qui a déjà le kit

C'est ainsi que ce guide a été éprouvé, et c'est ce qu'il faut refaire avant
chaque nouvelle version de la clé.

1. Dans l'Ubuntu habituelle : `make lab-down`. Toutes les distributions WSL
   partagent le même réseau : deux labs se disputeraient les ports.
2. **Coupez le Wi-Fi et débranchez le câble réseau.**
3. Déroulez la partie B telle quelle, à partir de B3.
4. Le contrôle `test_reseau_interne_interdit_toute_sortie` doit sortir en
   **SKIPPED** : c'est la preuve que la coupure était réelle. S'il sort en
   PASSED, le PC avait encore accès à Internet.
5. Pour effacer l'essai : partie D, puis rebranchez le réseau. L'Ubuntu
   habituelle n'a pas été touchée.

---

## Quand ça coince

| Symptôme | Cause | Remède |
|---|---|---|
| `command not found` sur `wsl` | commande Windows tapée dans Ubuntu | `exit`, puis la retaper dans l'invite Windows |
| `wsl --import` : `Wsl/ERROR_PATH_NOT_FOUND` | le dossier de destination n'existe pas | `mkdir C:\wsl\kibana-lab`, puis relancer |
| `wsl --import` : WSL n'est pas installé | WSL absent | partie B2 bis |
| `sha256sum` : un fichier `FAILED` | copie de la clé abîmée | recopier la clé |
| `installer-prerequis-horsligne.sh` : « À lancer en root » | ouvert en `formation` | `sudo bash /mnt/c/kit-media/installer-prerequis-horsligne.sh` |
| L'invite est encore en `#` après B4 | la distribution n'a pas redémarré | `exit`, `wsl --terminate kibana-lab`, `wsl -d kibana-lab` |
| `installer.sh` : « python3 -m venv a échoué » | ancien installateur, fichier temporaire laissé par root | `sudo rm -f /tmp/kit-venv.err`, puis relancer |
| `make mots-de-passe` : « 6 caractères au moins » | mot de passe trop court | en choisir un plus long : Elasticsearch l'exige |
| `make lab-up` bloqué à « Attente d'Elasticsearch » | lab lancé en root | refaire B4 à partir de la création de l'utilisateur ; le lab doit tourner en `formation` |
| `make lab-up` : port 9200 ou 5601 occupé | un autre lab tourne dans une autre distribution | `make lab-down` dans celle-ci |
| `make lab-up` : « iptables est introuvable » | prérequis incomplets | refaire B4 |
| La page de connexion refuse le mot de passe | mot de passe changé sans relancer le lab | `make lab-up` |
| `localhost:5601` ne répond pas dans le navigateur | lab arrêté (fenêtre Ubuntu fermée ?) | partie C, « Démarrer le lab » |
| Le guide refuse une bonne réponse | données rechargées sans recopier le guide | `cp dist/guide.html /mnt/c/kit-media/` |

---

## Ce qui a été vérifié, et ce qui ne l'a pas été

**Éprouvé le 23/09/2026 sur un vrai PC** — Windows 11 Pro 24H2, WSL 2.6.1 déjà
installé, Wi-Fi coupé : intégrité de la clé, prérequis (47 paquets, 0 non
configuré), import d'Ubuntu, installation du kit, démarrage du lab sous un
utilisateur ordinaire, données, corrigés, et 33 contrôles passés sans aucun
échec, dont celui qui prouve l'absence de réseau.

**Éprouvé sur la machine de fabrication** : les comptes `stagiaire` et `admin`
et leurs mots de passe fixés par `make mots-de-passe` (connexion acceptée,
ancien compte `formateur` retiré).

**Pas encore éprouvé** : l'installation de WSL sur un PC qui ne l'a pas
(B2 bis), et le mode réseau par défaut de WSL — le PC d'essai était réglé en
mode `mirrored`. En mode par défaut, WSL relaie lui aussi `localhost` vers
Windows ; si `http://localhost:5601` ne répondait pas, c'est le premier point à
examiner.
