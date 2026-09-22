# Installer le kit sur un poste Windows déconnecté du réseau

Ce document répond à une question posée telle quelle : « ça va être facile
d'installer tout ça sur un poste déconnecté du réseau, sous Windows ? »

**Non.** Comptez une demi-journée sur un poste coopératif, et une autorisation
préalable du service informatique sans laquelle l'opération n'a pas lieu. Ce
document dit exactement pourquoi, et exactement quoi faire.

## Statuts des affirmations

Ce kit s'interdit d'annoncer vérifié ce qui ne l'est pas. Chaque affirmation
technique de ce document porte donc une marque :

- **[mesuré]** — exécuté et observé sur la machine de fabrication (Linux
  x86_64, podman 4.9.3), sortie consignée.
- **[lu]** — établi en lisant un fichier du kit, référence donnée.
- **[connu]** — connaissance générale, **non vérifiée ici** : il n'y a pas de
  machine Windows dans la chaîne de fabrication. À contrôler sur place.

Les commandes Windows de ce document sont toutes **[connu]**. Elles sont
données parce qu'elles vous font gagner du temps, pas parce qu'elles ont été
éprouvées sur votre master.

---

## 1. Le point qui décide de tout : le kit est un logiciel Linux

Ce n'est pas une opinion, c'est ce que disent ses fichiers.

| Ce que le kit exige | Où c'est écrit | Sous Windows natif |
|---|---|---|
| `bash` | six scripts en `#!/usr/bin/env bash` | absent |
| `make` avec `SHELL := /usr/bin/env bash` | `Makefile` | absent |
| `.venv/bin/python` | `Makefile`, `lab/lab-up.sh`, `installer.sh` | le venv s'appelle `.venv\Scripts\python.exe` |
| `podman kube play` | `lab/lab-up.sh`, contrainte de `CLAUDE.md` | passe par une VM |
| `sha256sum`, `awk`, `sed`, `curl`, `df`, `ss` | scripts du lab | absents ou différents |

**[lu]** Conséquence : il n'existe pas d'installation « Windows native » de ce
kit, et il n'y en aura pas sans réécrire tout le pilotage en PowerShell.

**La seule architecture viable est donc : tout dans WSL2.** Une distribution
Linux à l'intérieur de Windows, qui contient podman, Python, le dépôt et le
lab. Windows ne sert qu'à deux choses : héberger cette distribution, et ouvrir
un navigateur sur `http://localhost:5601`.

Dans ce schéma, **aucune ligne du kit n'est à modifier**. Le pré-vol
(`lab/preflight.sh`) prend d'ailleurs sa branche Linux sous WSL2, puisque
`/proc/sys/vm/max_map_count` et `/proc/meminfo` y existent — c'est le bon
comportement **[lu]**.

> **Windows sur ARM ne convient pas.** Les images livrées sont `linux/amd64`
> **[mesuré]** : `arch=amd64, os=linux` pour les deux tars. Un Surface Pro X ou
> un portable Snapdragon ne démarrera pas le lab.

---

## 2. Ce qu'il faut faire autoriser AVANT de préparer quoi que ce soit

Quatre verrous. Si l'un ne cède pas, le kit ne tournera pas sur ce poste,
quels que soient les fichiers emportés. Faites-les instruire en **une seule
demande**, formulée en fonctionnalités Windows nommées.

1. **Virtualisation matérielle active dans le BIOS/UEFI** (Intel VT-x ou
   AMD-V). Suppose un accès au setup, donc souvent un passage physique.
2. **Fonctionnalités Windows** « Sous-système Windows pour Linux » et
   « Plateforme de machine virtuelle ». Élévation + redémarrage.
3. **Aucune GPO ne bloque WSL** (clé `HKLM\SOFTWARE\Policies\Microsoft\Windows\WSL`,
   règles AppLocker, retrait des droits d'administration locale).
4. **Exclusion d'analyse antivirus** sur le disque virtuel de la distribution,
   `%LOCALAPPDATA%\Packages\<distro>\LocalState\ext4.vhdx`. Sans elle,
   l'installation et le lab sont ralentis dans des proportions qui rendent la
   séance impraticable.

Ajoutez à la demande :

- **16 Go de RAM** sur le poste. Le lab en exige 6 **[lu]**, `lab/preflight.sh`
  ligne 16 ; sa suite de vérification en demande davantage, et WSL2 n'alloue
  par défaut qu'une fraction de la mémoire physique.
- **15 Go libres sur `C:`**. Le pré-vol exige 10 Go **[lu]**, plus la
  distribution et les fichiers intermédiaires.
- **Ports 9200 et 5601 libres.** Échappatoire documentée si un agent de
  sécurité les occupe : `KIT_PORT_ES=19200 KIT_PORT_KIBANA=15601 make lab-up` **[lu]**.

**Faites l'essai sur un poste connecté au même master.** Si `wsl --status`
répond et qu'une distribution démarre, vous saurez avant d'avoir gravé quoi
que ce soit. Si le master est verrouillé, vous l'apprendrez à un moment où
c'est encore réparable.

---

## 3. Côté connecté : constituer le média

### 3.1 Reconstruire l'archive — ce n'est pas optionnel

L'archive `kit-formation-kibana-9.5.3-20260922.tar.gz` qui existe aujourd'hui
**ne démarre le lab sur aucun poste neuf**. Défaut mesuré :

```
$ podman --root <magasin vierge> load -i images/elasticsearch.tar
Loaded image: mirror.gcr.io/library/elasticsearch:9.5.3

$ podman image exists mirror.gcr.io/library/elasticsearch@sha256:9020a0ab…
NON — l'image épinglée est introuvable
$ podman image exists mirror.gcr.io/library/elasticsearch@sha256:a9eaec68…
OUI
```

`podman save` resérialise l'image ; `podman load` lui donne un autre digest de
manifeste. Le pod référence celui du registre, `imagePullPolicy: Never`
interdit d'aller le chercher, `make lab-up` s'arrête sur `image not known`.

C'est corrigé dans le dépôt — `lab/rendre_pod.py` vérifie désormais que le
digest épinglé résout dans le magasin local et le réancre sinon — mais **la
correction ne voyage que dans une archive reconstruite** :

```bash
make guide && make package
```

### 3.2 Contrôler l'archive avant de la graver

```bash
ARCH=dist/kit-formation-kibana-9.5.3-<date du jour>
grep -c existe_localement $ARCH/lab/rendre_pod.py     # doit rendre ≥ 1
grep -c "5. Python"       $ARCH/lab/preflight.sh      # doit rendre 1
cat $ARCH/wheels/CIBLES.txt                           # doit lister vos cibles
wc -l < $ARCH/exigences.txt                           # doit couvrir 12 paquets
```

Puis l'empreinte, en chemin **relatif** :

```bash
cd dist && sha256sum kit-formation-kibana-*.tar.gz > kit-formation-kibana-*.tar.gz.sha256
```

> Le fichier `.sha256` portait un chemin absolu de la machine de fabrication
> **[mesuré]**. Sur le poste cible, `sha256sum -c` cherchait alors un fichier
> inexistant et échouait sur une archive pourtant intacte. Corrigé dans
> `outils/empaqueter.sh`, mais vérifiez : c'est une ligne, et elle coûte cher.

### 3.3 La question des wheels : vérifier la version de Python de la cible

Trois des dix-neuf wheels de l'ancienne archive portaient `cp311` **et**
`manylinux_x86_64` **[mesuré]** — `pyyaml`, `charset_normalizer`, `ruff`.
L'archive n'était installable que sur Linux x86_64 avec **CPython 3.11
exactement**. Ubuntu 24.04 livre 3.12 : `pip` refusait `pyyaml` dès la
première ligne.

`outils/empaqueter.sh` vendorise maintenant pour des cibles déclarées —
Linux x86_64 et macOS arm64, CPython 3.11 **et** 3.12 — et écrit
`wheels/CIBLES.txt`. **Lisez ce fichier, et faites correspondre la
distribution que vous emportez.**

### 3.4 Ce que l'archive ne contient pas, et qu'il faut ajouter au média

L'archive suppose un poste où podman et Python sont **déjà là**. Sur un poste
Windows vierge et hors réseau, rien ne l'est.

| À emporter | Taille indicative | Statut |
|---|---|---|
| L'archive reconstruite `.tar.gz` + son `.sha256` | ~1,5 Go **[mesuré]** | obligatoire |
| Paquet WSL au format MSI (`wsl.2.x.y.0.x64.msi`, releases GitHub `microsoft/WSL`) | ~100 Mo | **[connu]** |
| Racine de distribution Ubuntu 24.04 en tarball, pour `wsl --import` | 300–700 Mo | **[connu]** |
| Paquets `.deb` : `podman uidmap netavark aardvark-dns passt slirp4netns catatonit conmon fuse-overlayfs golang-github-containers-common make curl gawk iproute2 python3-venv` | ~300 Mo | **[connu]** |
| Les deux fichiers de configuration écrits d'avance (§4.3) | 1 Ko | — |

Les `.deb` se rapatrient depuis un Ubuntu 24.04 connecté :

```bash
mkdir debs && apt-get install --download-only -o Dir::Cache::archives="$PWD/debs" \
  podman uidmap netavark aardvark-dns passt slirp4netns catatonit conmon \
  fuse-overlayfs golang-github-containers-common make curl gawk iproute2 python3-venv
```

**Seulement si la recette complète doit tourner hors ligne** (les sept suites
`make verif-*`, et non la seule séance de formation) :

| À ajouter | Taille | Statut |
|---|---|---|
| Chromium de Playwright (`playwright install chromium`, puis copie de `~/.cache/ms-playwright`) | ~170 Mo | **[connu]** |
| Bibliothèques natives de WeasyPrint : `libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi8` | ~50 Mo | **[connu]** |

Si vous ne les emportez pas, **dites-le** : `make verif-parcours`,
`verif-corriges`, `verif-guide`, `verif-pdf` et `verif-package` ne
fonctionneront pas sur ce poste. `verif-lab` et `verif-donnees`, si.

### 3.5 Intégrité du média

`SHA256SUMS` ne se couvre pas lui-même, ne détecte aucun **ajout** de fichier,
et n'est signé par rien **[lu]**. Trois gestes :

1. Produire une empreinte du média entier, après copie :
   ```bash
   find . -type f -print0 | sort -z | xargs -0 sha256sum > MEDIA.SHA256
   ```
2. Transporter l'empreinte de l'archive **sur un autre canal que le média** :
   courriel signé, ticket, lecture au téléphone.
3. Si une PKI existe : `gpg --armor --detach-sign kit-...tar.gz`, clé publique
   par un autre canal.

**Imprimez la procédure.** En salle blanche, une instruction oubliée ne se
retélécharge pas.

---

## 4. Côté hors ligne : le poste Windows

### 4.1 Contrôler le média avant de l'ouvrir

`sha256sum` n'existe pas nativement sous Windows. Pour l'archive seule, en
invite de commandes :

```
certutil -hashfile kit-formation-kibana-9.5.3-<date>.tar.gz SHA256
```

Comparez au chiffre arrivé par l'autre canal. **[connu]**

### 4.2 Activer WSL2

En PowerShell **administrateur** **[connu]** :

```powershell
DISM /Online /Enable-Feature /FeatureName:Microsoft-Windows-Subsystem-Linux /All /NoRestart
DISM /Online /Enable-Feature /FeatureName:VirtualMachinePlatform /All /NoRestart
```

Redémarrer. Puis installer le MSI WSL (double-clic), et importer la
distribution **sans passer par le Microsoft Store**, qui n'est pas joignable :

```powershell
wsl --import kibana-lab C:\wsl\kibana-lab C:\media\ubuntu-24.04-rootfs.tar --version 2
wsl -d kibana-lab
```

### 4.3 Régler la VM WSL2 — les deux fichiers qui décident du succès

**`%UserProfile%\.wslconfig`**, côté Windows :

```ini
[wsl2]
memory=12GB
processors=4
swap=4GB
kernelCommandLine=sysctl.vm.max_map_count=262144
```

**`/etc/wsl.conf`**, dans la distribution :

```ini
[boot]
systemd=true
command = sysctl -w vm.max_map_count=262144
```

Puis, depuis Windows : `wsl --shutdown`, et relancer la distribution.

> **Pourquoi deux fichiers.** Elasticsearch exige `vm.max_map_count ≥ 262144`
> **[lu]**, et WSL2 démarre à 65530 **[connu]**. Le remède qu'affiche le
> pré-vol — `sudo sysctl -w`, puis `/etc/sysctl.d/99-elasticsearch.conf` — est
> exact mais **ne survit pas à un `wsl --shutdown`** sans `systemd=true`. Les
> deux lignes ci-dessus le rendent permanent par deux chemins indépendants :
> si l'un ne prend pas, l'autre tient. C'est le piège le plus coûteux de cette
> installation, parce qu'il se manifeste le deuxième jour, pas le premier.

### 4.4 Installer les prérequis dans la distribution

Dans `wsl -d kibana-lab` :

```bash
sudo dpkg -i /mnt/c/media/debs/*.deb
sudo apt-get install -f          # sans réseau, doit ne rien avoir à faire
podman --version                 # doit afficher 4.4 ou plus
python3 --version                # doit correspondre à wheels/CIBLES.txt
make --version
```

### 4.5 Poser le kit — dans le système de fichiers Linux

```bash
mkdir -p ~/kit && cd ~/kit
tar xzf /mnt/c/media/kit-formation-kibana-9.5.3-<date>.tar.gz
cd kit-formation-kibana-9.5.3-<date>
```

> **Jamais sous `/mnt/c`.** Le kit écrit `.env` en droits `600` **[lu]** ; sur
> un montage Windows, ces droits n'existent pas, et les entrées-sorties sont
> lentes d'un ordre de grandeur **[connu]**. Si l'archive a été extraite avec
> 7-Zip sur NTFS, le bit exécutable est perdu : `chmod +x installer.sh lab/*.sh`.

### 4.6 Installer et démarrer

```bash
bash lab/preflight.sh
```

Le pré-vol contrôle podman, `vm.max_map_count`, la mémoire, le disque, Python,
les images et les ports, et **affiche la commande exacte** pour chaque manque.
Il n'exécute jamais de `sudo` : c'est vous qui décidez **[lu]**.

```bash
./installer.sh
```

Il vérifie les empreintes — et **s'arrête** si l'une échoue, ce qui n'était
pas le cas auparavant **[mesuré]** — charge les images, crée l'environnement
Python depuis `wheels/` avec `--no-index`.

```bash
make lab-up
make data
make corriges
```

**`make data` reconstruit maintenant le guide automatiquement.** C'est
nécessaire et ce n'était pas fait : le générateur ancre sa fenêtre sur
l'instant du chargement — il n'accepte aucune ancre fixe, son `argparse` n'a
que trois arguments **[lu]** — donc chaque `make data` change les réponses,
donc les empreintes que le guide embarque. Sans reconstruction, **le stagiaire
saisit la bonne réponse et se la voit refuser**. C'est arrivé à la première
installation par un humain. `make lab-reset` fait de même désormais, ce qui
importe parce que le guide du formateur prescrit un reset avant chaque séance.

### 4.7 Contrôler

```bash
make verif-lab        # attendu : 19 passed, 1 skipped
make verif-donnees    # attendu : 14 passed
```

Ces deux-là suffisent à prouver que le lab est sain et que les données
correspondent au guide. Les cinq autres suites demandent Playwright et
WeasyPrint (§3.4).

### 4.8 Ouvrir

Depuis le navigateur **Windows** : `http://localhost:5601`. WSL2 redirige le
port automatiquement **[connu]** — avec deux réserves : cela peut demander
`localhostForwarding=true` dans `.wslconfig` selon la version, et un
redémarrage de la distribution remet parfois la redirection à plat.

Identifiant `stagiaire`, mot de passe engendré à l'installation dans `.env` :

```bash
grep STAGIAIRE_PASSWORD .env
```

Le guide s'ouvre depuis Windows en copiant le fichier :

```bash
cp dist/guide.html /mnt/c/Users/<vous>/Desktop/
```

C'est un fichier autonome : aucune requête réseau à l'ouverture, et c'est
vérifié par un contrôle dédié **[lu]**.

---

## 5. Combien de postes faut-il équiper ?

**Le stagiaire n'a besoin que d'un navigateur.** Le guide est autonome ; le
lab, lui, peut être partagé.

| | Topologie A — un lab par poste | Topologie B — un lab, N postes |
|---|---|---|
| Installations WSL2 | 9 | 1 |
| RAM totale | 9 × 16 Go | 16 Go sur le serveur |
| Disque | 9 × 15 Go | 15 Go |
| Temps d'installation | 9 × une demi-journée | une demi-journée |
| Ce que reçoit le stagiaire | tout | `guide.html` + une URL |

Kibana écoute sur `0.0.0.0` dans le pod **[lu]**, donc la topologie B est
acquise côté réseau sous Linux. **Deux réserves, honnêtement :**

1. **Un seul compte `stagiaire` existe** **[lu]**. Huit stagiaires partageant
   ce compte partagent aussi leurs recherches enregistrées et leurs tableaux
   de bord. Acceptable pour M0–M2, gênant à partir de M3 où chacun construit
   son écran.
2. **Sous Windows, la publication du port traverse WSL2.** Un poste tiers qui
   veut joindre le lab doit passer par une redirection `netsh interface portproxy`
   sur l'hôte Windows **[connu]** — ce n'est pas le `0.0.0.0` mesuré sous Linux.

**Recommandation pour un poste Windows hors réseau : topologie A, et un seul
poste.** Installez le lab sur la machine du formateur, projetez, et donnez aux
stagiaires le `guide.html` et les PDF sur clé. Vous éviterez huit fois les
quatre verrous du §2. Si chaque stagiaire doit manipuler, le coût réel est
neuf demi-journées d'installation, et il faut le dire avant de s'engager sur
une date.

---

## 6. Quand ça ne marche pas

| Symptôme | Cause | Remède |
|---|---|---|
| `podman kube play` : `image not known` | archive antérieure au correctif des digests | `rm lab/images.yaml` puis `make lab-up` — `rendre_pod.py` relève les digests du magasin **[mesuré]** |
| `pip` : `Could not find a version that satisfies pyyaml` | version de Python ≠ `wheels/CIBLES.txt` | installer la version listée, ou refaire `make package` côté connecté |
| `bad interpreter: /usr/bin/env bash^M` | fins de ligne CRLF | `sed -i 's/\r$//' lab/*.sh installer.sh` ; un `.gitattributes` protège désormais le dépôt |
| `./installer.sh: Permission denied` | extraction 7-Zip sur NTFS | `chmod +x installer.sh lab/*.sh` |
| `python3 -m venv` échoue | `python3-venv` absent | `sudo dpkg -i debs/python3-venv*.deb` — l'installateur le dit maintenant **[mesuré]** |
| Le pré-vol bloque sur `vm.max_map_count` | réglage non persistant | §4.3, les deux fichiers, puis `wsl --shutdown` |
| Cluster `red`, shards non alloués | disque plein | libérer de l'espace : Elasticsearch passe en lecture seule sous 5 % |
| Kibana reste `unavailable` | Elasticsearch pas prêt | attendre ; ES prêt en 36 s, `lab-up` complet sous 2 min sur 4 cœurs **[mesuré]** |
| Le guide refuse une bonne réponse | `make data` sans reconstruction du guide | `make guide-html` — ou plus rien, c'est automatique depuis |
| Quarantaine antivirus sur un `.tar` d'images | analyse temps réel | exclusion demandée au §2, point 4 ; `Get-ChildItem -Recurse \| Unblock-File` |

---

## 7. Ce que vous pouvez dire au service informatique

Le kit ne contient **aucune donnée réelle**, et ce n'est pas une déclaration
d'intention : deux contrôles nommés le vérifient à chaque construction,
`test_toutes_les_adresses_sont_reservees` et `test_tous_les_domaines_sont_reserves`
**[lu]**. Les adresses externes sont celles réservées à la documentation
(RFC 5737), les internes sont privées (RFC 1918), les domaines sont en `.test`
et `.example` (RFC 2606). Aucune capture, aucun nom d'hôte, aucune
configuration ne provient d'un système réel.

Le lab ne joint aucun registre à l'exécution : les images voyagent dans
l'archive et `imagePullPolicy: Never` interdit tout téléchargement **[lu]**.
Les cartes, la télémétrie et le fil d'actualité de Kibana sont coupés. La
licence est Basic, jamais un essai.

---

## 8. Récapitulatif honnête

**Ce qui est facile :** une fois WSL2 en place et les prérequis posés, le kit
s'installe en trois commandes et le lab démarre en moins de deux minutes.

**Ce qui ne l'est pas :** tout ce qui précède. Quatre autorisations à obtenir,
environ 2,5 Go de prérequis à constituer à la main côté connecté, deux
fichiers de configuration WSL2 sans lesquels le lab tombera le deuxième jour,
et une archive à reconstruire parce que celle qui existe ne démarre sur aucun
poste neuf.

**Ce qui reste non vérifié :** tout ce qui porte **[connu]** dans ce document.
Il n'y a pas de machine Windows dans cette chaîne de fabrication, et aucune
installation Windows n'a été réalisée. Le kit a été construit sur Linux et
installé une fois sur macOS — cette seule installation par un humain a révélé
sept défauts de portabilité que cinq relectures expertes n'avaient pas vus.
Attendez-vous à ce que la première installation Windows en révèle d'autres, et
prévoyez une journée d'essai sur un poste représentatif avant d'engager une
date de formation.
