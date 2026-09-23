# Installer le kit sur un PC Windows hors ligne

Deux temps : **préparer le support** sur un PC connecté, puis **installer** sur
le PC hors ligne. Le kit tourne dans une Ubuntu logée dans Windows par WSL2 ;
Windows ne sert qu'à l'héberger et à ouvrir Kibana dans son navigateur.

## Ce qui a été vérifié, et ce qui ne l'a pas été

**Vérifié le 23/09/2026**, de bout en bout, dans une copie neuve de l'Ubuntu
24.04 officielle pour WSL, privée de tout réseau : intégrité du support,
installation des prérequis (47 paquets, 0 non configuré), `installer.sh`
(empreintes, images chargées depuis les tars, Python depuis les wheels),
`make lab-up` (Kibana répond), données, guide reconstruit, corrigés, et
`verif-donnees` 14/14. La même procédure, en ligne, a donné 113 contrôles
passés sur un vrai PC Windows 11.

**Pas vérifié ici** : l'installation de WSL lui-même sur un Windows qui ne
l'a pas (paquet MSI et fonctionnalités Windows, voir `INSTALLATION_WINDOWS.md`
§2 et §4.2), et l'ouverture dans le navigateur Windows. La répétition sur un
vrai PC, Wi-Fi coupé, est l'étape qui les couvre.

Tapez **une commande à la fois**.

---

## Partie A — Préparer le support, sur un PC connecté

Sur un PC Windows où le kit tourne déjà en ligne (voir
`INSTALLATION_WINDOWS_UBUNTU.md`), dans son Ubuntu :

```
cd ~/kit/kibana-soc-kit
```

```
make lab-images
```

Attendu : deux lignes `digest épinglé tiré et étiqueté 9.5.3`. Ce sont ces
images-là qui partiront sur le support.

```
bash outils/preparer-media-windows.sh
```

Environ **7 minutes**. Attendu à la fin :
`Support prêt : /mnt/c/kit-media (2.0G)`. Le dossier **`C:\kit-media`**
contient :

| Fichier | Rôle |
|---|---|
| `ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz` (+ `.sha256`) | l'Ubuntu 24.04 officielle pour WSL, 340 Mo, empreinte vérifiée contre celle publiée par Canonical |
| `debs/` | 47 paquets système (podman, iptables, make, Python…) et leur index apt |
| `installer-prerequis-horsligne.sh` | les installe sans réseau |
| `kit-formation-kibana-9.5.3-<date>.tar.gz` (+ `.sha256`) | le kit : images, wheels, guide, PDF, 1,6 Go |
| `LISEZMOI.md` | ce document |
| `MEDIA.SHA256` | l'empreinte de chaque fichier du support |

Copiez `C:\kit-media` sur la clé ou le disque de transfert, **en entier**.

---

## Partie B — Installer, sur le PC hors ligne

### B1. Poser le support et le contrôler

Copiez le dossier en **`C:\kit-media`** : les commandes ci-dessous
supposent cet emplacement.

Si WSL n'est pas installé sur ce PC : voyez d'abord
`INSTALLATION_WINDOWS.md`, §2 et §4.2. Pour vérifier :

```
wsl --status
```

### B2. Importer l'Ubuntu du lab — invite de commandes Windows

Ces deux commandes se tapent dans **Windows** (`C:\…>`), pas dans Ubuntu : dans
Ubuntu, `wsl` n'existe pas.

```
mkdir C:\wsl\kibana-horsligne
```

**Mesuré le 23/09 sur un vrai PC** : sans ce dossier, `wsl --import` échoue
sur `Wsl/ERROR_PATH_NOT_FOUND`, un message qui laisse croire que c'est
l'image Ubuntu qui manque.

```
wsl --import kibana-horsligne C:\wsl\kibana-horsligne C:\kit-media\ubuntu-noble-wsl-amd64-24.04lts.rootfs.tar.gz --version 2
```

```
wsl -d kibana-horsligne
```

Vous êtes dans Ubuntu, **en root** : l'invite se termine par `#`. Toute la
suite se tape ici.

### B3. Contrôler le support

```
cd /mnt/c/kit-media
```

```
sha256sum -c --quiet MEDIA.SHA256 && echo "support intègre"
```

Attendu : `support intègre`. Toute autre sortie : **arrêtez**, le support est
abîmé ou incomplet.

### B4. Installer les prérequis

```
bash /mnt/c/kit-media/installer-prerequis-horsligne.sh
```

Attendu à la fin : `paquets non configurés : 0`, `podman version 4.9.3`,
`Python 3.12.3`, `venv disponible`.

### B5. Installer le kit

```
mkdir -p ~/kit
```

```
tar xzf /mnt/c/kit-media/kit-formation-kibana-*.tar.gz -C ~/kit
```

```
cd ~/kit/kit-formation-kibana-*
```

```
./installer.sh
```

Attendu : `empreintes conformes`, les deux images chargées, puis
`dépendances installées depuis wheels/`.

### B6. Démarrer

```
make lab-up
```

Attendu : le pré-vol, puis `Lab prêt. Kibana : http://localhost:5601`.

Au premier démarrage, le kit relève que les images chargées depuis les tars
n'ont pas le même digest que celles du registre, et le dit :
`digest épinglé introuvable dans le magasin local … Réancrage sur le magasin`.
**C'est normal**, c'est prévu.

```
make data
```

```
make data-epreuve
```

```
make corriges
```

Attendu : environ 380 000 documents par jeu, `dist/guide.html — 4.43 Mo`, puis
`[OK] Santé de la collecte` et `[OK] Vue IDS`.

### B7. Vérifier

```
make verif-lab verif-donnees
```

Attendu : `verif-donnees` **14 passed** ; `verif-lab` **18 à 19 passed**, avec
une ou deux lignes `SKIPPED` :

- `test_reseau_interne_interdit_toute_sortie` : **non exécuté sur un poste
  hors ligne**, et c'est honnête — il compare le réseau isolé du lab à un
  témoin qui, lui, doit pouvoir sortir ; sans réseau, personne ne sort, et la
  comparaison ne prouve rien.
- `test_lab_fonctionne_sur_reseau_interne` : non exécuté si la mémoire manque
  (il en faut 12 Go). S'il tourne et échoue, lancez d'abord
  `sysctl -w net.bridge.bridge-nf-call-iptables=0`, puis recommencez.

Aucun `FAILED` n'est attendu.

### B8. Ouvrir — côté Windows

Dans Edge ou Chrome : **http://localhost:5601**

- identifiant : `stagiaire`
- mot de passe, dans Ubuntu : `grep STAGIAIRE_PASSWORD .env`
- Space : **formation**

Le guide, à ouvrir depuis Windows :

```
cp dist/guide.html /mnt/c/kit-media/
```

puis double-cliquez `C:\kit-media\guide.html`.

---

## Pour une répétition sur un PC qui a déjà le kit en ligne

C'est ainsi que cette procédure se teste avant de partir en salle blanche.

1. Dans l'Ubuntu habituelle : `make lab-down`. Toutes les distributions WSL
   partagent le même réseau : deux labs se disputeraient les ports 9200 et
   5601.
2. **Coupez le Wi-Fi et débranchez le câble réseau.** Vérifiez dans
   l'invite de commandes Windows : `ping -n 2 1.1.1.1` doit échouer.
3. Déroulez la partie B telle quelle.
4. Pour tout effacer ensuite, invite de commandes Windows :
   `wsl --unregister kibana-horsligne`. Rebranchez le réseau ; l'Ubuntu
   habituelle n'a pas été touchée.

---

## Quand ça coince

| Symptôme | Cause | Remède |
|---|---|---|
| `sha256sum` signale un fichier `FAILED` | support abîmé pendant le transfert | recopier le dossier depuis la source |
| `wsl --import` : « WSL n'est pas installé » | WSL absent du PC | `INSTALLATION_WINDOWS.md` §4.2 |
| `wsl --import` : `Wsl/ERROR_PATH_NOT_FOUND` | le dossier de destination n'existe pas | `mkdir C:\wsl\kibana-horsligne`, puis relancer |
| `wsl` : « Command not found » | tapé dans Ubuntu | `exit`, puis la retaper dans l'invite de commandes Windows |
| `installer-prerequis-horsligne.sh` : « À lancer en root » | vous n'êtes pas root | `sudo bash /mnt/c/kit-media/installer-prerequis-horsligne.sh` |
| `make lab-up` : « iptables est introuvable » | prérequis incomplets | relancer B4 |
| `make lab-up` : port 9200 ou 5601 occupé | un autre lab tourne dans une autre distribution | `make lab-down` dans celle-ci |
| `localhost:5601` ne répond pas dans le navigateur | `make lab-up` n'a pas fini sur « Lab prêt » | relire sa sortie ; `podman logs kibana-soc-lab-kibana` |
| Le guide refuse une bonne réponse | données rechargées sans le guide | `make guide-html`, puis recopier `dist/guide.html` |
