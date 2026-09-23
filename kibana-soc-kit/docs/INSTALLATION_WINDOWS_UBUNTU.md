# Installer le kit sur Windows, par Ubuntu (WSL2)

Cette procédure est celle qui a été **déroulée et vérifiée de bout en bout**
le 23/09/2026 sur un poste réel : Windows 11 Pro 24H2 (build 26100), x86_64,
64 Go de RAM, WSL 2.6.1, Ubuntu 24.04, podman 4.9.3 sans root. Résultat de la
recette complète sur ce poste : **113 contrôles passés, 0 échec**, 9 non
exécutés parce qu'ils exigent une archive livrable absente du poste.

Chaque « Attendu » ci-dessous est ce que ce poste a réellement affiché.

Elle suppose un **accès à Internet** pendant l'installation. L'installation
sans réseau est traitée à part, dans `INSTALLATION_WINDOWS.md`, et n'a pas
encore été éprouvée de bout en bout.

Tapez **une commande à la fois**. Les lignes commençant par `#` sont des
explications, pas des commandes.

---

## 0. Ce qu'il faut sur le PC

| | Minimum | Pourquoi |
|---|---|---|
| Windows | 10 build 19041, ou 11 | WSL2 |
| Processeur | x86_64 (Intel ou AMD) | les images du lab sont `linux/amd64` : un PC ARM ne convient pas |
| Mémoire | 16 Go | le lab en prend 6 dans WSL2 ; la recette complète en veut 12 |
| Disque `C:` | 15 Go libres | Ubuntu, images, données |
| Virtualisation | active dans le BIOS | WSL2 |
| Docker Desktop | **fermé** pendant l'usage du lab | il partage le noyau de WSL2 |

Pour le vérifier en une minute, sans rien modifier, lancez le diagnostic
fourni, depuis l'invite de commandes Windows (cmd), dans le dossier où il a été
téléchargé :

```
cd %USERPROFILE%\Downloads
powershell -ExecutionPolicy Bypass -File diagnostic-windows.ps1
```

Attendu, en dernière ligne : `[OK] aucun blocage : le poste peut accueillir le lab dans WSL2`.

---

## 1. Créer l'Ubuntu du lab — côté Windows

Dans l'invite de commandes Windows :

```
wsl --install -d Ubuntu-24.04
```

Ubuntu demande un **nom d'utilisateur** et un **mot de passe** : ce dernier
servira pour `sudo`. Si WSL n'était pas encore installé, Windows demande un
redémarrage ; relancez la commande après.

On crée une distribution **dédiée**, même si une autre Ubuntu existe déjà : on
n'y touche pas, et le lab ne dépend pas de ce qu'on y a installé.

Pour rouvrir ce terminal plus tard : `wsl -d Ubuntu-24.04`, ou « Ubuntu 24.04
LTS » dans le menu Démarrer. Un simple `wsl` ouvrirait votre distribution par
défaut, peut-être une autre.

---

## 2. Les outils — dans Ubuntu

À partir d'ici, **tout se tape dans Ubuntu** (l'invite se termine par `$`).

```
sudo apt update
```

```
sudo apt install -y podman make python3-venv python3-pip git curl poppler-utils libharfbuzz-subset0
```

Vérifiez :

```
podman --version
```

Attendu : `podman version 4.9.3` (4.4 minimum).

```
python3 --version
```

Attendu : `Python 3.12.3` (3.11 minimum).

```
cat /proc/sys/vm/max_map_count
```

Attendu : `1048576`. Ubuntu 24.04 relève lui-même ce réglage, qu'Elasticsearch
exige à 262144 au moins : **rien à faire**. Si vous lisez 65530, voyez le §4.3
de `INSTALLATION_WINDOWS.md`.

---

## 3. Récupérer le kit — dans le dossier Linux, jamais sous `/mnt/c`

```
cd ~
```

```
git clone -b claude/kibana-soc-training-kit-yf6jr7 https://github.com/benoitdallery99-debug/KIBANA.git kit
```

```
cd ~/kit/kibana-soc-kit
```

Pourquoi pas `/mnt/c` : c'est le disque Windows vu depuis Ubuntu. Les droits
du fichier `.env`, qui contient les mots de passe, n'y fonctionnent pas, et
tout y est nettement plus lent.

---

## 4. Installer — dans Ubuntu

```
make venv
```

L'environnement Python du kit. Aucun message quand tout va bien.

```
make lab-images
```

Télécharge Elasticsearch et Kibana, **3,4 Go**, plusieurs minutes. Attendu à
la fin, deux lignes :

```
  elasticsearch : digest épinglé tiré et étiqueté 9.5.3
  kibana : digest épinglé tiré et étiqueté 9.5.3
```

Le kit tire les images **par leur empreinte exacte**, pas par leur étiquette :
l'étiquette `9.5.3` a été reconstruite en amont le 22/09, et seule l'empreinte
garantit les octets que la recette a vérifiés. L'avertissement
`"/" is not a shared mount` est sans effet sur ce lab.

```
make lab-up
```

Attendu : le pré-vol (8 rubriques `[OK]`, éventuellement un avertissement sur
`bridge-nf-call-iptables`), puis :

```
  Elasticsearch prêt (santé « green ») en 27s.
  Kibana disponible en 5s.
Lab prêt.  Kibana : http://localhost:5601
```

```
make data
```

Engendre et charge environ 380 000 événements synthétiques, **puis reconstruit
le guide** sur ces données. Attendu en dernière ligne :
`dist/guide.html — 4.43 Mo, 6 modules, 35 exercices, 17 questions de quiz`.

```
make data-epreuve
```

Le jeu de l'épreuve pratique, fermé aux stagiaires tant que le formateur ne
l'ouvre pas.

```
make corriges
```

Attendu : `[OK] Santé de la collecte`, `[OK] Vue IDS`, `[OK] export ndjson`.

---

## 5. Ouvrir — côté Windows

Dans Edge ou Chrome : **http://localhost:5601**

- identifiant : `stagiaire`
- mot de passe, à lire dans Ubuntu : `grep STAGIAIRE_PASSWORD .env`
- Space : **formation**

N'utilisez pas le compte `formateur` pour suivre le parcours : il voit les
corrigés.

Le guide se copie sur le Bureau Windows :

```
cp dist/guide.html /mnt/c/Users/$USER/Desktop/
```

Si votre nom Windows diffère de votre nom Ubuntu, remplacez `$USER` par le nom
du dossier Windows (`C:\Users\<nom>`), et si le Bureau est synchronisé par
OneDrive : `/mnt/c/Users/<nom>/OneDrive/Desktop/`.

---

## 6. Vérifier — facultatif, mais c'est la preuve

Une fois pour toutes :

```
.venv/bin/python -m playwright install --with-deps chromium
```

```
make guide
```

`make guide` produit aussi les sept PDF : environ 5 minutes.

Puis, à chaque recette :

```
sudo sysctl -w net.bridge.bridge-nf-call-iptables=0
```

```
make -k verif 2>&1 | tee ~/verif.log
```

```
grep -E "passed|failed|FAILED" ~/verif.log
```

Attendu, en 12 à 15 minutes : `20 passed`, `14 passed`, `33 passed`,
`9 passed`, `25 passed`, `10 passed`, puis `2 passed, 9 skipped`. Aucun
`failed`. De longs silences sont normaux : le navigateur rejoue les requêtes.

Le réglage `bridge-nf-call-iptables` vaut 1 par défaut sous WSL2 ; seul le
contrôle du réseau isolé en souffre, et le pré-vol le signale. Il est perdu au
redémarrage de WSL : à refaire avant chaque recette.

---

## 7. Au quotidien

| Pour | Dans Ubuntu, dans `~/kit/kibana-soc-kit` |
|---|---|
| Démarrer après un redémarrage du PC | `make lab-up` |
| Arrêter | `make lab-down` (les données sont conservées) |
| Repartir à neuf avant une séance | `make lab-reset` (1 min 49 s sur la machine de fabrication ; guide reconstruit automatiquement) |
| Ouvrir l'épreuve pratique | `make epreuve-ouvrir` |
| La refermer | `make epreuve-fermer` |
| Libérer les images inutiles | `podman image prune -f` |

Après `make data`, `make corriges` ou `make lab-reset`, `git status` montre
`data/manifest.json` et `corriges/tableaux-de-bord.ndjson` modifiés. **C'est
normal** : ils décrivent votre lab. Ne les committez pas. Pour récupérer une
mise à jour du kit malgré eux :

```
git checkout -- data/manifest.json corriges/tableaux-de-bord.ndjson
git pull
make data && make corriges
```

---

## 8. Quand ça coince

| Symptôme | Remède |
|---|---|
| `make lab-up` : `image not known` | `make lab-images`, puis `make lab-up` |
| Le pré-vol bloque sur la mémoire | fermer des applications, ou régler `memory=` dans `%UserProfile%\.wslconfig`, puis `wsl --shutdown` |
| Le pré-vol bloque sur `vm.max_map_count` | `INSTALLATION_WINDOWS.md` §4.3 |
| `localhost:5601` ne répond pas depuis Windows | `make lab-up` a-t-il fini sur « Lab prêt » ? Sinon `podman logs kibana-soc-lab-kibana` |
| Le guide refuse une bonne réponse | `make guide-html` : le guide doit suivre les données chargées |
| `git pull` refuse à cause de fichiers modifiés | voir le §7 |
| Les tests tournent sans rien afficher | c'est normal, ne pas interrompre |
