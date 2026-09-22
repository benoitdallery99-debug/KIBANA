# Capacités qualifiées — Kibana 9.5.3, licence Basic

**Objet.** Ce document dit, capacité par capacité, ce qui a le droit d'exister dans le kit de
formation. Il couvre toutes les capacités listées dans `docs/SPEC.md` §4.5. Il est la référence du
rédacteur du parcours en P3 : une capacité qui n'y figure pas en « oui » ne s'enseigne pas.

**Cible qualifiée** (`kit.config.yaml`, seule source de vérité) :

| Paramètre | Valeur |
|---|---|
| Version Elasticsearch / Kibana | **9.5.3** exactement |
| Licence | **Basic** auto‑générée (`xpack.license.self_generated.type: basic`), jamais de trial |
| Locale Kibana | `fr-FR` |
| Vue de solution du Space | `classic` |
| Space de travail | `formation` |

**Règle qui prime sur tout le reste** (`CLAUDE.md`) : *« Une fonctionnalité absente du lab n'existe
pas pour le parcours. »* La documentation officielle établit une présomption ; le lab tranche. Quand
les deux divergent, c'est le relevé du lab qui est écrit dans le tableau, et la divergence est dite.

---

## Comment ces constats ont été établis

> **Deux sources, et deux seulement.**
>
> **1. Recherche documentaire** — 270 constats, treize familles, avec pour chacun le badge
> `applies_to`, la citation, le chemin du fichier lu et son URL canonique. `www.elastic.co` est
> bloqué par la politique d'egress du poste de fabrication (403 au CONNECT ; écart **E1** du
> journal, contourné, pas résolu). La documentation a donc été lue **dans son dépôt source**,
> `github.com/elastic/docs-content`, qui est l'amont dont `elastic.co/docs` est engendré — une
> source officielle, pas un succédané. Clone local au commit `e74a5db` (21/09/2026). Les
> références qui ne vivent pas dans ce dépôt (référence ES|QL, agrégations, réglages Kibana,
> spécification de l'API Dashboards) ont été lues sur les branches **9.5** de `elastic/elasticsearch`
> et `elastic/kibana`, ou au tag **v9.5.3**, via `raw.githubusercontent.com`.
> Les URL `elastic.co` données en colonne « Source » sont donc **reconstruites** par la règle
> chemin → URL (`explore-analyze/dashboards.md` → `https://www.elastic.co/docs/explore-analyze/dashboards`)
> et n'ont pas pu être ouvertes depuis ce poste. Le libellé du lien est le chemin du fichier lu dans
> `docs-content`. Pour les pages qui ne vivent pas dans ce dépôt — référence ES|QL, agrégations,
> réglages et connecteurs Kibana — le libellé est le chemin canonique de la page de documentation ;
> le fichier réellement lu est `docs/<ce chemin>` dans `elastic/elasticsearch` ou `elastic/kibana`
> en branche 9.5, `reference/kibana/…` correspondant à `docs/reference/…`.
>
> **2. Relevé sur le lab** — `docs/capacites-lab.json`, produit par `lab/sonder_capacites.py` contre
> l'instance réelle du lab en licence Basic, dans le Space `formation`. C'est lui qui tranche.
>
> **Règle des badges `applies_to`** appliquée partout :
> `ga 9.5` ou `ga 9.5+` → **présent en 9.5.3** ; `ga 9.6+` → **absent de 9.5.3**, la capacité ne
> figure pas dans le parcours ; `=9.4` → cette version‑là seulement ; `9.4-9.5` → plage inclusive ;
> `preview` (avec ou sans numéro) → présent mais **aperçu technique**, signalé comme tel et jamais
> enseigné comme acquis ; badge sans numéro (`stack: ga`) → aucune borne de version, donc valide en
> 9.5.3. **Un badge de section ou en ligne supplante le frontmatter de la page** : la même page peut
> porter `ga` en tête et `ga 9.6` sur une ligne. Le dépôt `docs-content` est *cumulatif* et n'a pas de
> branche 9.5 : il décrit déjà de la 9.6, et seul le badge discrimine la version.
>
> **Ce que la documentation ne dit pas.** Sur **193 des 270 constats**, aucune page n'indique le
> niveau d'abonnement : `docs-content` renvoie à `elastic.co/subscriptions`, précisément la page
> bloquée. Là où les documentalistes ont comblé ce trou avec le **code source** de la version
> (champ `minimumLicenseRequired`, `minimalLicense`, `license_service.ts` au tag v9.5.3), la colonne
> « Basic » le signale par *(code v9.5.3)*. C'est une source officielle et citable, mais elle décrit
> une implémentation, pas un engagement commercial : seul le lab la confirme.
>
> **Honnêteté de la colonne « Confirmé en lab ».** `✔ oui` et `✘ non` ne sont écrits que lorsque
> `docs/capacites-lab.json` contient la preuve — code HTTP, valeur `enabled_in_license`, clé de
> traduction servie. Partout ailleurs : `— non sondé`. Un contrôle non exécuté est NON EXÉCUTÉ,
> jamais PASSÉ (`CLAUDE.md`). La section « Indéterminé à ce stade » recense ce qui reste ouvert.

**Ce que la sonde a réellement exercé sur le lab** (`docs/capacites-lab.json`) :

| Contrôle | Résultat |
|---|---|
| `GET /_license` | `basic`, `active` |
| `PUT /s/formation/api/dashboards/{id}` puis `GET`, `GET` liste, `DELETE` | 201 / 200 / 200 / 204, objet nettoyé |
| `POST /_query` (ES\|QL) sur `logs-*-formation` | 200, 384 592 documents comptés |
| `POST /s/formation/api/saved_objects/_export` (`index-pattern`) | 200, 1 137 octets |
| `GET /api/reporting/diagnose/screenshot` et `/api/reporting/jobs/list` | 404 et 404 |
| `GET /api/actions/connector_types` | 73 connecteurs, **2 utilisables** |
| `GET /api/alerting/rule_types` | 47 types, **41 utilisables** |
| `GET /api/features` | 53 fonctionnalités attribuables par Space, toutes `basic` |
| `GET /translations/fr-FR.json` | 60 705 clés traduites |

---

## 1. API Dashboards et tableau de bord as‑code

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| API Dashboards (REST), statut général | Dashboards API | oui (GA) | **oui (lab)** | 9.5 (aperçu en 9.4) | [explore-analyze/dashboards/create-dashboards-programmatically.md](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboards-programmatically) | ✔ oui |
| Créer ou remplacer un tableau de bord à identifiant choisi — **voie recommandée, idempotente** | Upsert a dashboard (`PUT /api/dashboards/{id}`) | oui | **oui (lab)** | 9.5 | [explore-analyze/dashboards/manage-dashboards-as-code.md](https://www.elastic.co/docs/explore-analyze/dashboards/manage-dashboards-as-code) | ✔ oui — HTTP 201 |
| Créer un tableau de bord à identifiant engendré | Create a dashboard (`POST /api/dashboards`) | oui | non précisé | 9.5 | [explore-analyze/kibana-data-exploration-learning-tutorial.md](https://www.elastic.co/docs/explore-analyze/kibana-data-exploration-learning-tutorial) | — non sondé |
| Lire et lister les tableaux de bord | Get / Search dashboards | oui | **oui (lab)** | 9.5 | [explore-analyze/dashboards/create-dashboards-programmatically.md](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboards-programmatically) | ✔ oui — 200 / 200 |
| Supprimer un tableau de bord | Delete a dashboard | oui | **oui (lab)** | 9.5 | [explore-analyze/dashboards/create-dashboards-programmatically.md](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboards-programmatically) | ✔ oui — 204 |
| Cibler un Space dans l'URL d'appel (`/s/{space}/…`) | Make API calls to a space | oui | **oui (lab)** | — (convention générale) | [deploy-manage/manage-spaces.md](https://www.elastic.co/docs/deploy-manage/manage-spaces) | ✔ oui |
| Export « JSON compatible API » d'un tableau de bord depuis l'UI | Export JSON | oui | non précisé | 9.5 (aperçu en 9.4) | [explore-analyze/dashboards/sharing.md](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | — non sondé |
| Export JSON d'un **panneau isolé** | Export a panel as JSON | **non** | sans objet | 9.6 (aperçu) | [explore-analyze/dashboards/sharing.md](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | — non sondé |
| API Visualizations (bibliothèque Lens) | Visualizations API | oui | non précisé | 9.5 | [explore-analyze/visualize/lens.md](https://www.elastic.co/docs/explore-analyze/visualize/lens) | — non sondé |

> **Route exacte.** Le lab a servi `PUT /s/formation/api/dashboards/{id}`. La route n'est **pas**
> `/api/dashboards/dashboard/{id}` : cette forme, proposée par un documentaliste, a été essayée puis
> corrigée. Voir « Points de vigilance ».

---

## 2. ES|QL

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Moteur ES\|QL côté Elasticsearch (`POST /_query`) | ES\|QL query API | oui | **oui (lab)** | 9.0 | [reference/query-languages/esql/limitations.md](https://www.elastic.co/docs/reference/query-languages/esql/limitations) | ✔ oui — 200 |
| Mode ES\|QL dans Discover | ES\|QL mode in Discover | oui | non précisé | 9.0 (page GA sans borne) | [explore-analyze/discover/try-esql.md](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — non sondé |
| Visualisation Lens construite à partir d'une requête ES\|QL | Visualization (query) panel | oui | non précisé | 9.0 | [explore-analyze/visualize/esorql.md](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — non sondé |
| Réglage d'activation — le nom est `enableESQL`, **`esql:enabled` n'existe pas** | enableESQL advanced setting | oui (actif par défaut) | non précisé | 9.0 | [reference/kibana/advanced-settings](https://www.elastic.co/docs/reference/kibana/advanced-settings) | — non sondé |
| `LIMIT` implicite à 1 000 lignes, plafond dur à 10 000 | Result set size limit | oui | non précisé | 9.0 | [reference/query-languages/esql/limitations.md](https://www.elastic.co/docs/reference/query-languages/esql/limitations) | — non sondé |
| Fonction `KQL()` — sensible à la casse sur `keyword` par défaut | ES\|QL `KQL` function, `case_insensitive` | oui | non précisé | 9.1 (GA) ; paramètre `options` en 9.3 | [reference/query-languages/esql/functions-operators/search-functions/kql.md](https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/search-functions/kql) | — non sondé |
| Mode rapide / approximation des `STATS` | Fast mode / `SET approximation` | aperçu | **non** (Enterprise, dit par la doc) | 9.4 (directive) ; 9.5 (bouton) | [explore-analyze/query-filter/languages/esql-kibana.md](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — non sondé |
| Assistance IA dans l'éditeur ES\|QL | Write and fix queries with AI | aperçu | **non** (Enterprise, dit par la doc) | 9.5 | [explore-analyze/query-filter/languages/esql-kibana.md](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — non sondé |
| Requête ES\|QL de départ configurable pour Discover | `discover:defaultEsqlQuery` | **non** | sans objet | 9.6 | [explore-analyze/discover/try-esql.md](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — non sondé |

> **Ce que le lab prouve, et ce qu'il ne prouve pas.** La sonde a obtenu un `200` sur `POST /_query`
> d'Elasticsearch : le moteur ES|QL fonctionne en Basic sur cette instance. Le second appel, passé
> par le proxy de la console Kibana, a renvoyé `400` — c'est un défaut de la sonde (paramétrage du
> proxy), pas un constat d'indisponibilité. **L'éditeur ES|QL de Discover et de Lens n'a donc pas
> été exercé** : voir « Indéterminé à ce stade ».

---

## 3. Contrôles de tableau de bord

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Contrôle « Liste d'options » | Options list control | oui | non précisé | 9.0 (page GA sans borne) | [explore-analyze/visualize/dashboard-controls.md](https://www.elastic.co/docs/explore-analyze/visualize/dashboard-controls) | — non sondé |
| Contrôle « Plage » (curseur de valeurs) | Range slider control | oui | non précisé | 9.0 | [explore-analyze/visualize/dashboard-controls.md](https://www.elastic.co/docs/explore-analyze/visualize/dashboard-controls) | — non sondé |
| Contrôle « Curseur temporel » | Time slider control | oui | non précisé | 9.0 | [explore-analyze/visualize/add-time-slider-controls.md](https://www.elastic.co/docs/explore-analyze/visualize/add-time-slider-controls) | — non sondé |
| Contrôle alimenté par une **requête ES\|QL** (onglet « Write a query ») | Write a query | oui (**GA en 9.5**) | non précisé | 9.5 | [explore-analyze/visualize/add-controls.md](https://www.elastic.co/docs/explore-analyze/visualize/add-controls) | — non sondé |
| **Contrôle de variable** ES\|QL (`?x` / `??x`) — à ne pas confondre avec la ligne précédente | Variable control | **aperçu** | non précisé | 9.0 (toujours en aperçu en 9.5.3) | [explore-analyze/visualize/add-variable-controls.md](https://www.elastic.co/docs/explore-analyze/visualize/add-variable-controls) | — non sondé |
| Notation CIDR dans une liste d'options sur champ `ip` | CIDR notation for IP address type fields | oui | non précisé | 9.4 | [explore-analyze/dashboards/using.md](https://www.elastic.co/docs/explore-analyze/dashboards/using) | — non sondé |

---

## 4. Sections pliables, panneau Liens, panneau Markdown

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Section pliable dans un tableau de bord | Collapsible section | oui | non précisé | 9.1 | [explore-analyze/dashboards/arrange-panels.md](https://www.elastic.co/docs/explore-analyze/dashboards/arrange-panels) | — non sondé (libellé fr‑FR relevé : voir §12) |
| Portée des contrôles non épinglés placés dans une section | Filter controls and sections | oui | non précisé | 9.4 | [explore-analyze/dashboards/arrange-panels.md](https://www.elastic.co/docs/explore-analyze/dashboards/arrange-panels) | — non sondé |
| Panneau Liens | Links panel | oui | non précisé | — (page GA sans borne) | [explore-analyze/visualize/link-panels.md](https://www.elastic.co/docs/explore-analyze/visualize/link-panels) | — non sondé |
| Panneau texte / Markdown, éditeur en ligne | Text panels / Markdown Text | oui | non précisé | — (9.2 pour l'éditeur en ligne) | [explore-analyze/visualize/text-panels.md](https://www.elastic.co/docs/explore-analyze/visualize/text-panels) | — non sondé |
| Panneau Markdown réutilisable (bibliothèque) et détachement | Save to library / Unlink from library | oui | non précisé | 9.4 | [explore-analyze/visualize/text-panels.md](https://www.elastic.co/docs/explore-analyze/visualize/text-panels) | — non sondé |
| Limites : 1 000 panneaux par tableau de bord, 100 contrôles épinglés | Panel limits | oui | non précisé | 9.4 | [explore-analyze/dashboards/arrange-panels.md](https://www.elastic.co/docs/explore-analyze/dashboards/arrange-panels) | — non sondé |

---

## 5. Drilldowns (fr‑FR : « explorations »)

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Drilldown tableau de bord → tableau de bord | Dashboard drilldown / Go to dashboard | oui | **oui** *(code v9.5.3 : aucun gate)* | < 9.0 | [explore-analyze/dashboards/drilldowns.md](https://www.elastic.co/docs/explore-analyze/dashboards/drilldowns) | — non sondé |
| Drilldown Discover depuis un panneau Lens | Discover drilldown / Open in Discover | oui | **oui** *(code v9.5.3 : aucun gate)* | < 9.0 | [explore-analyze/dashboards/drilldowns.md](https://www.elastic.co/docs/explore-analyze/dashboards/drilldowns) | — non sondé |
| Drilldown Discover sur un panneau Lens **ES\|QL** | Discover drilldowns on ES\|QL Lens visualizations | oui | **oui** *(code v9.5.3)* | 9.5 | [explore-analyze/dashboards/drilldowns.md](https://www.elastic.co/docs/explore-analyze/dashboards/drilldowns) | — non sondé |
| **Drilldown URL** | URL drilldown / Go to URL | oui | **non** — Gold minimum *(code v9.5.3 : `minimalLicense: 'gold'`)* | < 9.0 | [explore-analyze/dashboards/drilldowns.md](https://www.elastic.co/docs/explore-analyze/dashboards/drilldowns) | — non sondé |
| Modèle d'URL Handlebars du drilldown URL | URL templating language | aperçu (bêta déclaré en dur) | **non** (suit le drilldown URL) | < 9.0 | [explore-analyze/dashboards/drilldowns.md](https://www.elastic.co/docs/explore-analyze/dashboards/drilldowns) | — non sondé |
| Aucun drilldown depuis un champ calculé (formule Lens, `EVAL`, `STATS`) | Computed fields do not support drilldown actions | oui (limitation) | oui | 9.4 pour l'énoncé badgé | [explore-analyze/dashboards/using.md](https://www.elastic.co/docs/explore-analyze/dashboards/using) | — non sondé |

> **Asymétrie déterminante pour le parcours.** La documentation ne mentionne **jamais** de niveau
> d'abonnement pour les drilldowns : un lecteur qui s'en tiendrait à elle croirait les trois types
> équivalents. Le code de la version cible dit l'inverse : dashboard et Discover sans garde, URL
> avec `minimalLicense: 'gold'`, **double** (création désactivée *et* exécution refusée). Aucun de
> ces points n'a été sondé sur le lab : ils sont en tête de la liste des tests à faire.

---

## 6. Passage d'un panneau vers Discover

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Action de menu « Explorer dans Discover » d'un panneau Lens — **active par défaut** | Explore in Discover | oui | non précisé | — (page GA sans borne) | [explore-analyze/kibana-data-exploration-learning-tutorial.md](https://www.elastic.co/docs/explore-analyze/kibana-data-exploration-learning-tutorial) | — non sondé |
| Action « Explorer les données sous‑jacentes » (plugin `discoverEnhanced`) — **désactivée par défaut** | Explore underlying data (`exploreDataInContextMenu`, défaut `false`) | oui, mais inactive | non précisé | — | [explore-analyze/visualize/manage-panels.md](https://www.elastic.co/docs/explore-analyze/visualize/manage-panels) | — non sondé |
| Clic sur un point d'une série pour l'ouvrir dans Discover — **désactivé par défaut** | Series data interactions (`exploreDataInChart`, défaut `false`) | oui, mais inactive | non précisé | — | [explore-analyze/visualize/manage-panels.md](https://www.elastic.co/docs/explore-analyze/visualize/manage-panels) | — non sondé |
| Conditions du pivot : une seule data view, un seul calque, aucun décalage temporel | the panel must use only one data view | oui | non précisé | — | [explore-analyze/visualize/manage-panels.md](https://www.elastic.co/docs/explore-analyze/visualize/manage-panels) | — non sondé |

> **Deux mécanismes homonymes, un seul actif.** La page `manage-panels.md` documente en détail
> l'action qui ne marche pas sans réglage `kibana.yml`, et ne nomme jamais celle qui marche. Le kit
> enseigne l'action Lens « Explorer dans Discover » ; l'autre est mentionnée comme option
> d'administration. Seule la condition « une seule data view » est documentée : « un seul calque »
> et « aucun décalage temporel » viennent du code et restent à vérifier.

---

## 7. Lens : formules, lignes de référence, couleurs, approximations

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Formules Lens | Formula | oui | non précisé | — (page GA sans borne) | [explore-analyze/visualize/lens.md](https://www.elastic.co/docs/explore-analyze/visualize/lens) | — non sondé |
| Filtre KQL dans une formule (`kql='…'`) — ratio de filtre | Filter ratio | oui | non précisé | — | [explore-analyze/visualize/lens.md](https://www.elastic.co/docs/explore-analyze/visualize/lens) | — non sondé |
| Lignes de référence (statique, fonction rapide, formule) | Reference lines | oui | non précisé | — | [explore-analyze/visualize/lens.md](https://www.elastic.co/docs/explore-analyze/visualize/lens) | — non sondé |
| Annotations | Annotations | **aperçu** | non précisé | — (badge `preview` sans numéro) | [explore-analyze/visualize/lens.md](https://www.elastic.co/docs/explore-analyze/visualize/lens) | — non sondé |
| Affectation de couleurs à des termes | Assign colors to terms | oui | non précisé | 9.1 (GA) | [explore-analyze/visualize/lens.md](https://www.elastic.co/docs/explore-analyze/visualize/lens) | — non sondé |
| **« Unique count » est approximatif** (agrégation `cardinality`) | Unique count / cardinality aggregation | oui | non précisé | — | [explore-analyze/dashboards/create-dashboard-of-panels-with-web-server-data.md](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboard-of-panels-with-web-server-data) | — non sondé |
| Seuil de précision de `cardinality` : **3 000 par défaut**, 40 000 au maximum | `precision_threshold` | oui | oui | — (identique sur 9.2 et 9.5) | [reference/aggregations/search-aggregations-metrics-cardinality-aggregation.md](https://www.elastic.co/docs/reference/aggregations/search-aggregations-metrics-cardinality-aggregation) | — non sondé |
| Barre de progression dans une table | Progress bar (column appearance) | **non** | sans objet | 9.6 | [explore-analyze/visualize/charts/tables.md](https://www.elastic.co/docs/explore-analyze/visualize/charts/tables) | — non sondé |

> **La documentation ne parle jamais de licence pour Lens.** Sur tout `explore-analyze/visualize/` et
> `explore-analyze/dashboards/`, une seule mention d'abonnement existe, et elle porte sur les rapports
> PDF/PNG. Aucune capacité de cette famille ne peut donc être déclarée « disponible en Basic » sur
> preuve documentaire : d'où « non précisé » partout, et le test lab correspondant.

---

## 8. Export, partage et rapports

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Rapport CSV d'une session Discover enregistrée | CSV Reports / Export > CSV | oui | **oui** (doc explicite, onglet « Basic license ») | 9.0 | [explore-analyze/report-and-share.md](https://www.elastic.co/docs/explore-analyze/report-and-share) | — non sondé |
| Rapport CSV depuis un panneau « session Discover » d'un tableau de bord | CSV report from a saved Discover session panel | oui | **oui** | 9.0 | [deploy-manage/kibana-reporting-configuration.md](https://www.elastic.co/docs/deploy-manage/kibana-reporting-configuration) | — non sondé |
| Téléchargement CSV d'un panneau (menu du panneau, ou Inspecter > Données) | Download CSV (Formatted / Raw) | oui | non précisé | 9.0 | [explore-analyze/dashboards/sharing.md](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | — non sondé |
| **Rapport PDF** d'un tableau de bord | Export as PDF / PDF reports | oui (dans le produit) | **non** — « PDF reports are a subscription feature » | 9.0 | [explore-analyze/dashboards/sharing.md](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | ✘ non — reporting non servi (404) |
| **Rapport PNG** d'un tableau de bord | Export as PNG / PNG reports | oui (dans le produit) | **non** — « PNG reports are a subscription feature » | 9.0 | [explore-analyze/report-and-share.md](https://www.elastic.co/docs/explore-analyze/report-and-share) | ✘ non — reporting non servi (404) |
| **Planification d'exports récurrents**, y compris en CSV | Schedule export / Schedule report generation | oui | **non** *(code v9.5.3 : Gold ; la doc ne le dit pas)* | 9.3 (GA) | [explore-analyze/report-and-share/automating-report-generation.md](https://www.elastic.co/docs/explore-analyze/report-and-share/automating-report-generation) | — non sondé |
| Génération automatisée par POST URL | Create a POST URL | oui | **oui** | 9.0 | [explore-analyze/report-and-share/automating-report-generation.md](https://www.elastic.co/docs/explore-analyze/report-and-share/automating-report-generation) | — non sondé |

> **Ce que le `404` du lab prouve, et ce qu'il ne prouve pas.** Les deux routes de reporting sondées
> répondent `404`, donc la chaîne de reporting n'est pas servie sur ce lab. Un `404` n'est pas le
> `403 « Your basic license does not support PDF Reporting »` que décrit le code : il peut aussi
> signaler une route renommée. Le verdict « PDF/PNG hors Basic » reste donc **documentaire**
> (citation explicite), et le test qui le rendrait factuel est décrit plus bas.

---

## 9. Alerting : types de règles et connecteurs

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Règle « Recherche Elasticsearch » (`.es-query`) | Elasticsearch query rule type | oui | **oui (lab)** | 9.0 | [explore-analyze/alerting/alerts/rule-type-es-query.md](https://www.elastic.co/docs/explore-analyze/alerting/alerts/rule-type-es-query) | ✔ oui |
| Règle « Seuil de l'index » (`.index-threshold`) | Index threshold rule type | oui | **oui (lab)** | 9.0 | [explore-analyze/alerting/alerts/rule-type-index-threshold.md](https://www.elastic.co/docs/explore-analyze/alerting/alerts/rule-type-index-threshold) | ✔ oui |
| Règle « Seuil personnalisé » (`observability.rules.custom_threshold`) | Custom threshold rule | oui | **oui (lab)** | 9.0 | [solutions/observability/incident-management/create-custom-threshold-rule.md](https://www.elastic.co/docs/solutions/observability/incident-management/create-custom-threshold-rule) | ✔ oui |
| Custom threshold : alerte « no data » et groupement (`Group alerts by`) | Trigger "no data" alerts / Group alerts by | oui | oui (le type est utilisable) | 9.0 ; 9.4 pour les 3 options | [solutions/observability/incident-management/create-custom-threshold-rule.md](https://www.elastic.co/docs/solutions/observability/incident-management/create-custom-threshold-rule) | — non sondé (option non exercée) |
| Règles de détection Elastic Security (`siem.*` : requête, EQL, ES\|QL, seuil, nouveaux termes…) | Security detection rules | oui | **oui (lab)** — 9 types utilisables | 9.0 | [explore-analyze/alerting/alerts/rule-types.md](https://www.elastic.co/docs/explore-analyze/alerting/alerts/rule-types) | ✔ oui |
| Règle « Suivi de l'endiguement » (`.geo-containment`) | Tracking containment rule type | oui | **non** — Gold | 9.0 | [explore-analyze/alerting/alerts/geo-alerting.md](https://www.elastic.co/docs/explore-analyze/alerting/alerts/geo-alerting) | ✘ non |
| Règles de détection d'anomalies ML et intégrité des tâches ML | Machine learning rules | oui | **non** — Platinum | 9.0 | [explore-analyze/alerting/alerts/rule-types.md](https://www.elastic.co/docs/explore-analyze/alerting/alerts/rule-types) | ✘ non |
| Règles « Taux d'avancement SLO », « Anomalie de durée Uptime », « ES\|QL Rule » (Streams) | SLO burn rate / duration anomaly / Streams ES\|QL rule | oui | **non** — Platinum, Platinum, Enterprise | — | [explore-analyze/alerting/alerts/rule-types.md](https://www.elastic.co/docs/explore-analyze/alerting/alerts/rule-types) | ✘ non |
| Connecteur « Index » (`.index`) | Index connector | oui | **oui (lab)** | 9.0 | [reference/kibana/connectors-kibana/index-action-type.md](https://www.elastic.co/docs/reference/kibana/connectors-kibana/index-action-type) | ✔ oui |
| Connecteur « Server log » (`.server-log`) | Server log connector | oui | **oui (lab)** | 9.0 | [reference/kibana/connectors-kibana/server-log-action-type.md](https://www.elastic.co/docs/reference/kibana/connectors-kibana/server-log-action-type) | ✔ oui |
| **Les 71 autres connecteurs** (Email, Slack, Webhook, PagerDuty… Gold ; Cases… Platinum) | Paid commercial connector types | oui (présents) | **non** | 9.0 | [deploy-manage/manage-connectors.md](https://www.elastic.co/docs/deploy-manage/manage-connectors) | ✘ non |

> **Le relevé du lab est exhaustif et reproductible.** `GET /api/actions/connector_types` →
> **2 connecteurs sur 73** portent `enabled_in_license: true`, exactement `.index` et `.server-log` :
> l'attendu de SPEC §4.5 est confirmé par l'instance, pas seulement par la doc.
> `GET /api/alerting/rule_types` → **41 types sur 47**. Les six exclus sont ceux des trois lignes
> « non » ci‑dessus. Ces deux appels sont à reproduire tels quels devant les stagiaires en M5 : c'est
> la meilleure preuve possible de ce que la licence autorise.
> Prérequis de configuration non sondés, mais imposés par SPEC §4.1 : `xpack.encryptedSavedObjects.encryptionKey`
> (sans elle, l'alerting de M5 est indisponible) et `search.allow_expensive_queries` à `true`
> ([explore-analyze/alerting/alerts/alerting-setup.md](https://www.elastic.co/docs/explore-analyze/alerting/alerts/alerting-setup)).

---

## 10. Spaces et privilèges

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Spaces Kibana (cloisonnement des objets enregistrés) | Kibana Spaces | oui | **oui** *(code v9.5.3 : `check('spaces','basic')`)* | — | [deploy-manage/manage-spaces.md](https://www.elastic.co/docs/deploy-manage/manage-spaces) | ✔ oui — Space `formation` servi |
| Vue de solution d'un Space (cible : `classic`) | Solution view | oui | non précisé | 8.16 | [deploy-manage/manage-spaces.md](https://www.elastic.co/docs/deploy-manage/manage-spaces) | — non sondé |
| Privilèges Kibana **de base** par Space (`all` / `read`) | Base privileges | oui | **oui** | — | [deploy-manage/users-roles/cluster-or-deployment-auth/kibana-privileges.md](https://www.elastic.co/docs/deploy-manage/users-roles/cluster-or-deployment-auth/kibana-privileges) | — non sondé |
| Privilèges **par fonctionnalité** par Space | Feature privileges | oui | **oui (lab)** — 53 fonctionnalités, toutes `basic` | — | [deploy-manage/users-roles/cluster-or-deployment-auth/kibana-privileges.md](https://www.elastic.co/docs/deploy-manage/users-roles/cluster-or-deployment-auth/kibana-privileges) | ✔ oui |
| **Sous‑privilèges** de fonctionnalité (p. ex. `download_csv_report` seul) | Sub-feature privileges | oui | **non** — « If you have a Basic license, sub-feature privileges are unavailable » | — | [deploy-manage/users-roles/cluster-or-deployment-auth/kibana-privileges.md](https://www.elastic.co/docs/deploy-manage/users-roles/cluster-or-deployment-auth/kibana-privileges) | — non sondé |
| Sécurité au niveau document (DLS) et au niveau champ (FLS) | Document-level / Field-level security | oui | **non** — Platinum | — | [deploy-manage/users-roles/cluster-or-deployment-auth/kibana-role-management.md](https://www.elastic.co/docs/deploy-manage/users-roles/cluster-or-deployment-auth/kibana-role-management) | — non sondé |

---

## 11. Objets enregistrés, export/import, data views

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Export ndjson des objets enregistrés (UI et API) | Export saved objects | oui | **oui (lab)** | — | [explore-analyze/find-and-organize/saved-objects.md](https://www.elastic.co/docs/explore-analyze/find-and-organize/saved-objects) | ✔ oui — 200, 1 137 octets |
| Import ndjson des objets enregistrés (UI et API) | Import saved objects | oui | non précisé | — | [explore-analyze/find-and-organize/saved-objects.md](https://www.elastic.co/docs/explore-analyze/find-and-organize/saved-objects) | — non sondé |
| **Compatibilité d'un export entre versions** : même version, mineure plus récente de la même majeure, ou majeure suivante | Compatibility across versions | oui | non précisé | — | [explore-analyze/find-and-organize/saved-objects.md](https://www.elastic.co/docs/explore-analyze/find-and-organize/saved-objects) | — non sondé |
| Copier un objet vers un autre Space (UI et API) | Copy to spaces | oui | **oui** *(code v9.5.3)* | — | [explore-analyze/find-and-organize/saved-objects.md](https://www.elastic.co/docs/explore-analyze/find-and-organize/saved-objects) | — non sondé |
| Imposer l'identifiant d'une data view à la création (UI et API) | Custom data view ID | oui | non précisé | — | [explore-analyze/find-and-organize/data-views/create-data-view.md](https://www.elastic.co/docs/explore-analyze/find-and-organize/data-views/create-data-view) | — non sondé |
| Plafonds d'export et d'import | `savedObjects.maxImportExportSize` / `maxImportPayloadBytes` | oui | non précisé | — | [explore-analyze/find-and-organize/saved-objects.md](https://www.elastic.co/docs/explore-analyze/find-and-organize/saved-objects) | — non sondé |

---

## 12. Terminologie de la version, en fr‑FR

Les libellés marqués `✔ oui` ont été **relevés dans les traductions que le lab sert réellement**
(`GET /translations/fr-FR.json`, 60 705 clés), jamais traduits de tête.

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Recherche enregistrée → **« Session Discover »** (clé `discover.savedSearch.savedObjectName`) | Discover session (et non « saved search ») | oui | sans objet | 8.18 / 9.0 pour le renommage | [explore-analyze/discover/save-open-search.md](https://www.elastic.co/docs/explore-analyze/discover/save-open-search) | ✔ oui |
| Application → **« Tableaux de bord »** (clé `dashboard.dashboardPageTitle`) | Dashboards | oui | sans objet | — | [explore-analyze/dashboards.md](https://www.elastic.co/docs/explore-analyze/dashboards) | ✔ oui |
| Section pliable → **« Section pliable »** (clé `dashboard.collapsibleSection.displayName`) | Collapsible section | oui | sans objet | 9.1 | [explore-analyze/dashboards/arrange-panels.md](https://www.elastic.co/docs/explore-analyze/dashboards/arrange-panels) | ✔ oui |
| Téléchargement CSV → **« Télécharger CSV »** | Download CSV | oui | sans objet | — | [explore-analyze/dashboards/sharing.md](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | ✔ oui |
| « data view » est le terme officiel ; « index pattern » ne subsiste que comme **libellé du champ** du formulaire de création | data view / Index pattern (field) | oui | sans objet | 8.0 (renommage) | [explore-analyze/find-and-organize/data-views.md](https://www.elastic.co/docs/explore-analyze/find-and-organize/data-views) | ✘ non — clé `dataViews.savedObjectName` absente de la traduction servie |
| « drilldown » se dit **« exploration »** dans l'UI fr‑FR | drilldown | oui | sans objet | — | [explore-analyze/dashboards/drilldowns.md](https://www.elastic.co/docs/explore-analyze/dashboards/drilldowns) | — non sondé |
| Activation de la locale : `i18n.locale` est **déprécié** en 9.5, remplacé par `i18n.defaultLocale` + `i18n.locales` | i18n.defaultLocale / i18n.locales | oui | non précisé | 9.5 | [reference/kibana/configuration-reference/internationalization-settings](https://www.elastic.co/docs/reference/kibana/configuration-reference/internationalization-settings) | — non sondé |

---

## 13. Données et index (support des exercices)

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Schéma de nommage des data streams : `<type>-<dataset>-<namespace>` | data stream naming scheme | oui | non précisé | — | [reference/fleet/data-streams.md](https://www.elastic.co/docs/reference/fleet/data-streams) | — non sondé |
| `logsdb` appliqué par défaut aux nouveaux data streams `logs-*-*` | logsdb index mode enabled by default | oui | **oui** | 9.0 | [manage-data/data-store/data-streams/logs-data-stream.md](https://www.elastic.co/docs/manage-data/data-store/data-streams/logs-data-stream) | — non sondé |
| `_source` synthétique de `logsdb` | synthetic `_source` | oui | **non** — repli automatique sur le `_source` stocké | — | [manage-data/data-store/data-streams/logs-data-stream-configure.md](https://www.elastic.co/docs/manage-data/data-store/data-streams/logs-data-stream-configure) | — non sondé |
| Réglages imposés par `logsdb` : `ignore_malformed`, `ignore_above: 8191`, tri forcé, `best_compression` | Logsdb settings reference | oui | **oui** | 9.0 | [manage-data/data-store/data-streams/logs-data-stream-configure.md](https://www.elastic.co/docs/manage-data/data-store/data-streams/logs-data-stream-configure) | — non sondé |
| `failure store` activée par défaut sur `logs-*-*` | failure store | oui | non précisé | 9.1 (9.2 pour l'activation automatique) | [manage-data/data-store/data-streams/failure-store.md](https://www.elastic.co/docs/manage-data/data-store/data-streams/failure-store) | — non sondé |

---

## 14. Conséquences pour le parcours

Rappel de la règle de SPEC §4.5 : *« Une capacité absente n'apparaît pas dans le parcours, sauf dans un
encadré “Hors licence Basic” quand son absence surprendrait. »* Ce qui suit est la liste des décisions
à appliquer, module par module. Les décisions marquées **(lab)** sont adossées à
`docs/capacites-lab.json`, et pas seulement à la documentation.

### 14.1 Encadrés « Hors licence Basic » à prévoir

Quatre absences surprendraient un analyste SOC et méritent donc d'être **montrées, expliquées et
justifiées** plutôt que passées sous silence.

| Ce qui manque | Où le dire | Pourquoi ça surprendrait | Ce que le kit propose à la place |
|---|---|---|---|
| **Rapports PDF et PNG** d'un dashboard | **M4**, au moment du partage du dashboard « Vue IDS » | « exporter mon tableau de bord en PDF pour le comité » est la première demande d'un chef de salle. L'exemple est d'ailleurs celui que cite SPEC §4.5 | *Download CSV* d'un panneau, capture d'écran, et partage du dashboard par lien |
| **Connecteurs Email, Slack, Webhook** **(lab)** | **M5**, section alerting | « et ça m'envoie un mail ? » est la question n° 1 sur l'alerting | Connecteurs **Index** (réinjection dans un index dédié, puis dashboard ou Discover sur cet index) et **Server log** |
| **Drilldown URL** (pivot d'une valeur vers un outil externe) | **M3**, section drilldowns | pivoter d'une IP vers un outil d'enrichissement ou un ticket est un geste SOC quotidien | Drilldown **dashboard → dashboard** et **Discover** (tous deux en Basic), plus le panneau **Liens** pour un lien statique |
| **Sécurité au niveau document et au niveau champ** (DLS / FLS) | **M5**, section rôles et Spaces | « chaque analyste ne voit que son périmètre » est une exigence courante en SOC mutualisé | Un motif d'index distinct par périmètre + un Space distinct : le seul cloisonnement possible en Basic |

### 14.2 Capacités retirées du parcours, sans encadré

**Retirées parce que hors Basic.** Planification d'exports récurrents et envoi par courriel, y compris
au format CSV (**M5**) ; connecteur **Cases** et donc le scénario « une alerte crée automatiquement un
cas » (**M5**) ; règles **Tracking containment** (Gold) et **Anomaly detection** (Platinum) — **(lab)** : le lab ne
sert que 41 types de règles sur 47 et 2 connecteurs sur 73 (**M5**) ; privilèges d'index
sur clusters distants et ES|QL en recherche multi-clusters — à annoncer en une phrase dès **M1** pour
que personne n'essaie `FROM cluster:index` ; **Fleet space-aware**, donc pas de politiques d'agents par
Space (**M5**) ; **Agent Builder**, partout ; le mode **Fast mode / approximation** d'ES|QL et
l'**assistance IA** de l'éditeur (**M1**) ; les **sous-privilèges** de fonctionnalité, ce qui ramène
tout **M5** à une granularité `all` / `read` par fonctionnalité et par Space ; l'application **Graph**
et ses « drilldown URLs » homonymes ; l'optimisation `route_on_sort_fields` de logsdb.

Deux notes de confort pédagogique : la documentation affirme que, sans licence Enterprise ni connecteur
LLM, **les éléments d'IA de l'éditeur ES|QL ne s'affichent pas du tout** — l'écran du stagiaire restera
donc cohérent avec le support ; et le synthetic `_source` de logsdb, faute d'abonnement, se replie sur
le `_source` d'origine, donc le danger « logsdb altère mes documents » ne devrait pas se matérialiser.

**Retirées parce qu'absentes en 9.5.3 (arrivent en 9.6).** Export JSON d'un **panneau isolé**, y compris
pour les panneaux Liens, Markdown et les contrôles (**M3**, **M5**) ; **API Links** et **API Markdowns**
(**M5**) ; paramètres `tag_names` et `excluded_tag_names` de `GET /api/dashboards`, donc **filtrer par
identifiants de tags et non par noms** (**M5**) ; réglage `discover:defaultEsqlQuery` — ne rien
promettre sur la requête de départ (**M1**) ; décoration **barre de progression** dans les tableaux
Lens (**M2**) ; **panneaux personnalisés** HTML/CSS.

**Retirées ou dégradées parce qu'en aperçu technique.** Rien de ce qui est en `preview` n'entre dans un
exercice noté. Sont concernés : les **contrôles de variables** ES|QL — les exercices de **M3** portent
sur le contrôle **alimenté par une requête** (onglet *Write a query*), GA en 9.5, et le variable control
reste une démonstration facultative étiquetée ; la **barre de recherche KQL** de l'éditeur ES|QL, qui
est pourtant le meilleur pont pédagogique KQL → ES|QL de **M1** et mérite une démonstration étiquetée ;
l'**affichage groupé** `STATS BY` et les **sparklines** (**M1**) ; l'**éditeur d'index de
correspondance** ; l'**API Tags** ; le **provider Terraform**, réduit à une mention d'une ligne en
**M5** ; le **système d'alerting v2**, à mentionner pour que personne ne le découvre par accident.
Deux aperçus doivent néanmoins être **montrés**, parce que le stagiaire les aura sous les yeux : la
**refonte du sélecteur de temps** (*Presets*, *Calendar*, *Custom range*, badgée `preview 9.5`), que
**M0** décrira d'après la capture du lab et non d'après la documentation ; et le badge
**« VERSION D'ÉVALUATION TECHNIQUE »** du volet d'export JSON, que **M5** doit expliquer plutôt que
taire, puisque la documentation annonce cet export en GA.

### 14.3 Capacités confirmées qui structurent le parcours

- **M0** — Spaces et vue de solution `classic`, data view à ID fixe, time filter (sous réserve du test
  d'interface, voir §16), terminologie de la version.
- **M1** — Discover en KQL, Lucene **et** ES|QL, ce dernier étant GA sans réserve. Casse sur keyword,
  CIDR sur champ `ip`, filtres, Discover session.
- **M2** — Lens : métrique, barres, lignes, tableau, heatmap ; **formules** ; **lignes de référence**
  avec les trois modes de placement, dont le placement **par formule** qui permet un seuil dynamique ;
  couleur par valeur, palette **Severity** (9.4) ; et le piège de l'*unique count*.
- **M3** — Contrôles liste d'options, plage et curseur temporel ; contrôle alimenté par requête ES|QL
  (nouveauté 9.5) ; **sections repliables** (9.1) et contrôles **désépinglés** à portée de section
  (9.4) ; panneau **Liens** ; panneau **Markdown Text** réutilisable en bibliothèque (9.4) ; drilldowns
  dashboard et Discover ; passage d'un panneau vers Discover.
- **M4** — Capstone. **Contrainte de conception issue de cette qualification** : les panneaux de type
  `map` et `alerts_table` sont refusés en écriture par l'API Dashboards et silencieusement retirés en
  lecture. Un dashboard SOC contenant une carte géographique ou une table d'alertes **ne peut pas être
  géré en as-code en 9.5.3**. Les deux dashboards corrigés doivent donc être conçus sans ces types.
  Seconde contrainte : la table des dernières alertes doit rester à **un seul calque, sans décalage
  temporel, sur une seule data view**, faute de quoi le passage vers Discover disparaît du menu.
  **Troisième contrainte, établie sur le lab** : l'API Dashboards **refuse** une source de données qui
  référence une data view par son identifiant (`"type": "data_view"` → **HTTP 400**) ; seul
  `"type": "data_view_spec"`, c'est-à-dire le motif d'index **en ligne**, est accepté. Les deux dashboards
  corrigés construits par l'API portent donc leur motif en dur.
- **M5** — Export et import ndjson et sa règle de compatibilité (**export confirmé sur le lab**, HTTP 200) ;
  data views à ID fixe ; **API Dashboards**, GA en 9.5, **servie en Basic et confirmée sur le lab**
  (création 201, relecture 200, liste 200, suppression 204 dans le Space `formation`), donc pleinement
  enseignable ; règles **Elasticsearch query**, **Index threshold** et **Custom threshold** avec alerte
  « no data » par groupe — c'est exactement ce qu'exige le scénario S6 du générateur, et **les trois
  types sont confirmés utilisables sur le lab** ; connecteurs **Index** et **Server log**, les deux seuls
  sur 73 (**lab**) ; rôles et Spaces.
  **Nuance de portabilité à enseigner, établie sur le lab** : un dashboard construit par l'API porte son
  motif d'index en ligne (`data_view_spec`), et **son export ndjson ne contient donc aucune référence**.
  L'identifiant fixe de data view garde tout son sens pour les dashboards construits dans l'interface puis
  transportés en ndjson — c'est bien ce que M5 enseigne — mais il ne s'applique pas à la voie as-code.

### 14.4 Deux décisions à prendre avant d'écrire P3

1. **Template d'index maison, ou pas.** Un template maison prioritaire sur `logs-*-*` remplace
   entièrement le template intégré : on perd d'un coup `logsdb`, les mappings ECS, les champs
   `data_stream.*` en `constant_keyword`, le pipeline `logs@default-pipeline` et la failure store. Si le
   générateur pose son propre template (SPEC §5.1 l'exige, « de priorité supérieure aux templates
   intégrés »), il **doit** reprendre `composed_of: ["ecs@mappings","logs@mappings","logs@settings"]`.
   Priorité recommandée par la documentation : **501**.
2. **Quel chemin vers Discover enseigner.** *Explorer dans Discover* (action du plugin Lens, active par
   défaut) et non *Explorer les données sous-jacentes* (plugin `discoverEnhanced`, désactivée par
   défaut depuis 7.14). Aucune modification de `kibana.yml` ne doit être nécessaire au parcours, ce qui
   est cohérent avec la règle de `CLAUDE.md` : « réglages par défaut de Kibana conservés ».

---

## 15. Points de vigilance

Chaque point ci-dessous est un piège constaté dans la documentation, à reprendre dans la fiche mémo,
dans le quiz, ou dans un exercice de SPEC §6.3.

**1. `Unique count` est approximatif, et la documentation se contredit.** Le tutoriel dit
« approximates the number of unique values »
([explore-analyze/dashboards/create-dashboard-of-panels-with-web-server-data.md:69](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboard-of-panels-with-web-server-data)),
la référence des agrégations de cartes dit « the number of distinct values » sans nuance, et **la
référence embarquée dans l'éditeur Lens — celle que le stagiaire lira — ne mentionne pas du tout
l'approximation**. Seule la référence Elasticsearch chiffre : algorithme HyperLogLog++, seuil de
précision par défaut **3 000**, maximum 40 000
([elasticsearch@9.5 search-aggregations-metrics-cardinality-aggregation.md:61](https://www.elastic.co/docs/reference/aggregations/search-aggregations-metrics-cardinality-aggregation)).
Aucune option de seuil n'est exposée par Lens : l'analyste subit le défaut. C'est la justification
documentaire de la règle de `CLAUDE.md` : **toute réponse fondée sur un unique count reste < 3 000**.

**2. Trois sources d'approximation silencieuse, à regrouper dans un même chapitre de M2.** Au-delà de
l'unique count : le biais de shard des *Top values*, que *Enable accuracy mode* atténue au prix de la
charge cluster ; et l'**échantillonnage de couche**, dont la documentation dit elle-même
« This increases performance but reduces accuracy »
([explore-analyze/visualize/lens.md:294](https://www.elastic.co/docs/explore-analyze/visualize/lens)).
Un même panneau peut cumuler les trois. Message à faire passer : **un chiffre affiché par Lens n'est pas
un chiffre exact par défaut.**

**3. Casse de `KQL()` sur les champs keyword.** Il n'existe pas d'encadré d'avertissement, mais trois
constats convergents : le paramètre nommé `case_insensitive` de `KQL()` vaut **`false` par défaut** et
ne concerne explicitement que les champs keyword (paramètres nommés disponibles depuis 9.3) ; la règle
KQL générale veut que « on keyword, numeric, date, or boolean fields, the value must match exactly,
including punctuation and case »
([explore-analyze/query-filter/languages/kql.md:66](https://www.elastic.co/docs/explore-analyze/query-filter/languages/kql)) ;
et sans `MATCH`/`QSTR`/`KQL`, un champ `text` se comporte comme un `keyword`
([elasticsearch@9.5 limitations.md:190-194](https://www.elastic.co/docs/reference/query-languages/esql/limitations)).
À ne pas confondre avec l'insensibilité à la casse des **mots-clés du langage** (`FROM`, `from`, `From`).
En SOC, c'est la source classique de faux négatifs sur `user.name`, `host.name`, `process.name`.
`CLAUDE.md` interdit déjà de valider une requête KQL avec la fonction `KQL()` : ce constat l'étaye.

**4. Compatibilité des exports NDJSON — la règle est confirmée, avec une précision.** Verbatim :
« saved objects can only be imported into the same version, a newer minor on the same major, or the next
major »
([explore-analyze/find-and-organize/saved-objects.md:110](https://www.elastic.co/docs/explore-analyze/find-and-organize/saved-objects)).
La précision que la table de la même page rend visible : **« la majeure suivante » n'impose aucune
contrainte de mineure** (7.8.1 → 8.3.0 est accepté) **mais s'arrête à une majeure** (7.8.1 → 9.0.0 est
refusé). Depuis 9.5.3, le domaine est donc : 9.5.3, 9.6+, et 10.x. À ajouter : ne jamais retirer
`coreMigrationVersion` ni `typeMigrationVersion` d'un ndjson édité à la main.

**5. `index.mode` : `logsdb` s'applique par défaut, et c'est un réglage statique.** Depuis 9.0, tout
**nouveau** data stream dont le nom correspond à `logs-*-*` reçoit `index.mode: logsdb`, posé par le
template intégré `logs` de priorité 100
([manage-data/data-store/data-streams/logs-data-stream.md:19-21](https://www.elastic.co/docs/manage-data/data-store/data-streams/logs-data-stream)).
Conséquences gratuites et par défaut : `ignore_malformed: true`, `ignore_above: 8191`, tri forcé sur
`host.name` puis `@timestamp` avec injection automatique de `host.name`, codec `best_compression`.
`index.mode` étant **statique**, un changement ne prend effet qu'au prochain rollover, sur le nouvel
index de backing.

**6. Sur `logs-*-*`, presque rien n'échoue visiblement à l'ingestion.** `ignore_malformed: true` fait
qu'un champ mal formé est **silencieusement ignoré** (placé dans `_ignored`) au lieu de rejeter le
document ; les champs dynamiques au-delà de la limite sont ignorés de même ; et la **failure store**,
activée par défaut sur `logs-*-*` depuis 9.2, fait qu'un conflit de mapping renvoie au client une
**réponse de succès** portant un simple drapeau de redirection
([manage-data/data-store/data-streams/failure-store.md:45](https://www.elastic.co/docs/manage-data/data-store/data-streams/failure-store)).
Tout exercice « ce document est rejeté » doit donc être conçu avec ce comportement en tête, et M5 doit
apprendre à regarder `_ignored` et la failure store, pas seulement les codes de retour.

**7. Nommage des data streams : lire `<source>.<type>` comme un seul champ.** Le schéma officiel est
`<type>-<dataset>-<namespace>`, le point n'étant **pas** un séparateur de niveau mais un caractère
*interne au dataset* (`logs-nginx.access-prod`, dataset = `nginx.access`)
([reference/fleet/data-streams.md:45-54](https://www.elastic.co/docs/reference/fleet/data-streams)).
La forme de SPEC §5.1, `logs-<source>.<type>-<namespace>`, est **conforme** à condition de lire
`<source>.<type>` comme étant le dataset — par exemple `logs-suricata.alert-formation`. Corollaire : la
contrainte « pas de tiret » porte sur **tout** le dataset `<source>.<type>` et, d'après Fleet, aussi sur
le namespace, chacun plafonné à 100 caractères.

**8. Le mot « contrôle ES|QL » recouvre deux choses de statuts opposés.** Le *variable control*
(`?x` / `??x` lié à une requête de visualisation) est en **aperçu technique** depuis 9.0 et l'est
toujours en 9.5.3 ; le contrôle liste d'options ou plage **alimenté par une requête** ES|QL (onglet
*Write a query*) est **GA depuis 9.5**. Confondre les deux revient à enseigner comme stable ce qui est
en preview.

**9. Le panneau texte n'a pas été renommé dans le sens que l'on croit.** En 9.0-9.1 l'entrée de menu
s'appelait **Text** ; depuis **9.2** elle s'appelle **Markdown Text**. Quatre graphies coexistent en
9.5.3 pour le même objet : la page de documentation s'intitule *Text panels*, le menu d'ajout dit
*Markdown Text*, le type d'objet et le filtre de la bibliothèque disent *Markdown*, et le tableau de
synthèse écrit *Markdown text*
([explore-analyze/visualize/text-panels.md:11, :21-23](https://www.elastic.co/docs/explore-analyze/visualize/text-panels)).
Un support qui dit « ajoutez un panneau Text » envoie le stagiaire chercher une entrée disparue.

**10. Depuis un dashboard, « Exporter » ne donne plus un ndjson.** En 9.5, le menu *Export* d'un
dashboard produit un **JSON compatible avec l'API Dashboards** ; le ndjson ne s'obtient plus que par
Stack Management → Saved Objects
([explore-analyze/dashboards/sharing.md:97-137](https://www.elastic.co/docs/explore-analyze/dashboards/sharing)).
Tout support recyclé d'une version antérieure à 9.4 est faux sur ce point. Règle à enseigner : **JSON
pour le versionnage as-code** (lisible, mais **lossy** — les propriétés non supportées sont
silencieusement retirées), **NDJSON pour la sauvegarde et la migration** (fidèle, et seul format accepté
par `_import`).

**11. `PUT` remplace intégralement, il n'existe pas de `PATCH`.** La spécification avertit : « This is a
full replacement. Any panels not included in the request body are permanently removed. » L'enchaînement
correct est donc `GET` → modifier → `PUT`. C'est l'erreur numéro un des débutants sur l'API Dashboards.

**12. Les défauts de l'UI et de l'API sont opposés.** UI d'export : objets liés inclus par défaut ; API
`_export` : `includeReferencesDeep` vaut **false**. UI d'import : écrasement par défaut ; API `_import` :
`overwrite` vaut **false**. API `_copy_saved_objects` : `createNewCopies` vaut **true**, donc l'objet
copié reçoit un **nouvel identifiant**. Sur les trois routes, `overwrite` et `createNewCopies` sont
mutuellement exclusifs.

**13. Le tri par en-tête de colonne en ES|QL ment sur le « top » réel.** « This performs client-side
sorting and only sorts the rows that were retrieved by the query »
([explore-analyze/discover/try-esql.md:176-184](https://www.elastic.co/docs/explore-analyze/discover/try-esql)) :
cliquer pour trier « les plus gros volumes » ne trie que les 1 000 premières lignes remontées. À
enseigner avec `SORT … DESC | LIMIT n`.

**14. Un tableau de résultats peut être partiel sans rupture visuelle forte.** Une requête ES|QL qui
expire (`search:timeout`, 10 minutes par défaut) ou qui est annulée affiche des **résultats partiels**
([explore-analyze/discover/discover-get-started.md:303-328](https://www.elastic.co/docs/explore-analyze/discover/discover-get-started)).
Sur une chasse longue, l'analyste peut conclure sur un jeu incomplet.

**15. Une valeur issue d'un champ calculé n'est ni filtrable au clic ni utilisable comme drilldown.**
Cela vaut pour les formules Lens, les résultats d'agrégation et les colonnes `EVAL` ou `STATS` d'ES|QL
([explore-analyze/dashboards/using.md:76](https://www.elastic.co/docs/explore-analyze/dashboards/using)).
Règle de conception : **toujours conserver au moins une dimension issue d'un champ réel de l'index**
à côté des colonnes calculées, sinon l'analyste perd le pivot au clic. Vaut directement pour les
panneaux de M4.

**16. Un drilldown URL importé depuis un environnement Gold est muet, sans erreur.** Le verrou de
licence porte à la fois sur la création et sur l'exécution : le dashboard s'importe sans erreur, puis
le drilldown n'est ni proposé au clic ni éditable (ligne en erreur dans *Gérer les explorations*).
Piège de migration classique, à scénariser.

**17. `Explore underlying data` est désactivée par défaut depuis 7.14.** Et c'est pourtant la seule des
deux actions que documente `manage-panels.md`. Le chemin qui fonctionne sans configuration est
*Explore in Discover*, fournie par le plugin Lens
([explore-analyze/visualize/manage-panels.md:77](https://www.elastic.co/docs/explore-analyze/visualize/manage-panels) ;
défaut `false` : `elastic/kibana`@9.5 `general-settings.yml:1620-1642`).

**18. Un template maison prioritaire fait perdre tout le template intégré.** Voir §14.4, point 1.

**19. La documentation `elastic.co` est cumulative : elle décrit aussi 9.6.** Depuis 9.0, Elastic ne
publie plus un jeu de documentation par mineure
([get-started/versioning-availability.md:28](https://www.elastic.co/docs/get-started/versioning-availability)).
Un formateur qui lit une page sans regarder le badge croira disponible ce qui arrive en 9.6 — l'export
JSON d'un panneau isolé en est l'exemple parfait. **Prévoir un avertissement explicite dans le guide** :
« la documentation en ligne décrit des versions postérieures à votre lab ; lisez le badge ». À
l'inverse, la documentation conserve les descriptions des interfaces 9.0-9.3 dans des notes badgées :
un stagiaire qui les suit ne trouvera pas les menus.

**20. La traduction fr-FR est incomplète, et cela se verra dans les captures.** Cas établi : les clés
`dashboard.navigationOptions.useFiltersLabel`, `.useTimeRange` et `.openInNewTab` sont **absentes** du
fichier de traduction fr-FR de 9.5.3. Les trois bascules de l'éditeur de drilldown dashboard
s'afficheront donc **en anglais dans une interface française**. De même, la traduction de « data view »
flotte d'un écran à l'autre. Conséquence opérationnelle, déjà inscrite dans `CLAUDE.md` : **toutes les
captures doivent être produites sur le lab réel en fr-FR**, jamais reprises de la documentation, qui est
en anglais et décrit parfois un écran différent.


**21. `[1025 TO *]` relève de Lucene, pas de KQL — et l'échec est silencieux.** La syntaxe d'intervalle
entre crochets est celle de Lucene. Saisie dans une barre de requête en **KQL**, elle ne lève pas
d'erreur : elle renvoie zéro résultat. La forme KQL correcte est `destination.port >= 1025`, KQL
disposant de `>=`, `<=`, `>` et `<`
([explore-analyze/query-filter/languages/kql.md](https://www.elastic.co/docs/explore-analyze/query-filter/languages/kql)).
Le constat d'échec silencieux vient du lab et est inscrit dans `docs/SPEC.md` §6.3 et `CLAUDE.md` ;
il **n'est pas couvert par `docs/capacites-lab.json`** et doit donc être reproduit et **capturé** avant
d'entrer dans le guide. Corollaires à enseigner dans le même exercice : l'existence s'écrit `champ:*` en
KQL et `_exists_:champ` en Lucene.

**22. La route de l'API Dashboards est `/api/dashboards/{id}`, pas `/api/dashboards/dashboard/{id}`.**
La seconde forme circule dans les notes de qualification ; elle est fausse. Le lab tranche :
`PUT /s/formation/api/dashboards/{id}` répond **201**, `GET` **200**, `DELETE` **204**. Préférer `PUT`
avec un identifiant choisi, idempotent et rejouable, plutôt que `POST`, qui engendre un nouvel
identifiant à chaque appel
([explore-analyze/dashboards/manage-dashboards-as-code.md](https://www.elastic.co/docs/explore-analyze/dashboards/manage-dashboards-as-code)).

**23. L'API Dashboards n'accepte pas une data view référencée par identifiant.** Établi sur le lab :
une source de données déclarée `"type": "data_view"` est refusée par **HTTP 400** ; seul
`"type": "data_view_spec"` — le motif d'index **en ligne** — passe. Conséquence directe, à enseigner en
**M5** : l'export ndjson d'un dashboard construit par l'API **ne porte aucune référence**, là où celui
d'un dashboard construit dans l'interface en porte une vers la data view. Les deux voies ne produisent
donc pas le même objet, et la promesse documentaire « garder les références portables » ne vaut que pour
la seconde.

**24. Un dashboard importé dans un autre Space reçoit un nouvel identifiant.** Établi sur le lab : le
dashboard est un objet **partageable entre Spaces** ; importer un identifiant qui existe déjà dans un
autre Space **crée une copie** sous un nouvel identifiant, rendu dans `destinationId`, **même avec
`createNewCopies=false`**. Un exercice de M5 qui vérifierait « l'objet a bien gardé son identifiant »
échouerait donc pour une bonne raison. À enseigner avec le point 12 : les identifiants ne se
conservent qu'à l'intérieur d'un même Space.

---

## 16. Indéterminé à ce stade

Cette section existe pour que le document reste honnête. Rien de ce qui suit n'a pu être tranché par la
documentation, et rien ne sera écrit dans le parcours avant que le test correspondant ait été exécuté
en P1 — à l'exception de ce que le relevé sur le lab a depuis tranché, récapitulé juste en dessous.
Les points **A** à **D** sont des **contradictions entre deux sources ou deux documentalistes**,
signalées comme telles.

### Ce que le relevé sur le lab a déjà tranché

Le sondage de `lab/sonder_capacites.py` a fermé d'un coup plusieurs questions que la documentation
laissait ouvertes, et elles ne figurent donc plus ci-dessous : la licence effective (`basic`, `active`) ;
la disponibilité **réelle** de l'API Dashboards en Basic ; la liste **exhaustive** des types de règles
(41 sur 47) et des connecteurs (**2 sur 73**, `.index` et `.server-log`) ; les 53 fonctionnalités
attribuables par Space, toutes `basic` ; l'export ndjson des objets enregistrés ; et quatre libellés
fr-FR relevés dans les traductions servies. Deux réserves demeurent sur ce relevé :

- le sondage d'ES|QL **par Kibana** a répondu `400` — défaut de paramétrage du proxy de console dans la
  sonde, **pas** un constat d'indisponibilité ; seul le moteur Elasticsearch a été exercé (HTTP 200) ;
- les deux routes de reporting ont répondu `404`. Un `404` n'est pas le `403` de licence décrit par le
  code : il n'exclut pas une route renommée. Le verdict « PDF/PNG hors Basic » reste **documentaire**.

### Les 193 constats sans niveau d'abonnement, par famille

Sur les 270 constats documentaires, **193 ne précisent pas le niveau d'abonnement** — la documentation
renvoie à `elastic.co/subscriptions`, page bloquée — et la sonde n'en a couvert qu'une part. Tant qu'une
ligne figure ici, le rédacteur du parcours ne l'écrit pas comme acquise.

| Famille | Constats sans niveau d'abonnement | Ce qui reste ouvert | Test qui tranche |
|---|---|---|---|
| **Contrôles** | 24 / 25 | aucun des six contrôles n'a été créé sur le lab | créer un dashboard portant une liste d'options, une plage, un curseur temporel et un contrôle *Write a query* : les quatre créés tranchent toute la famille |
| **ES\|QL dans l'interface** | 29 / 32 | ni Discover ni Lens n'ont été ouverts en mode ES\|QL | ouvrir Discover en mode ES\|QL, exécuter un `STATS`, créer un panneau *Visualization (query)* ; refaire le sondage Kibana avec `POST /api/console/proxy?path=%2F_query&method=POST` |
| **Panneaux (section pliable, Liens, Markdown)** | 17 / 17 | aucun type de panneau relevé sur l'instance | ouvrir le menu **Ajouter** d'un dashboard et capturer la liste complète des types offerts sous cette licence |
| **Drilldowns** | 7 / 18 | le gate Gold du drilldown URL vient du **code**, pas du lab | relever quelles tuiles sont proposées dans « Créer une exploration » et lesquelles portent « Niveau de licence insuffisant » |
| **Passage panneau → Discover** | 11 / 11 | ni l'action Lens ni ses conditions n'ont été vérifiées | poser un panneau Lens mono-calque, vérifier la présence de l'action, puis refaire avec deux calques et avec un `shift=` |
| **Lens** | 22 / 23 | aucune formule ni ligne de référence construite | construire une formule avec `kql=`, une ligne de référence, une couleur par valeur ; **et trancher le point B ci-dessous** |
| **Export et rapports** | 3 / 12 | le `404` ne distingue pas route renommée et refus de licence | ouvrir le menu **Export** d'un dashboard, puis lire le corps de la réponse de la route de génération |
| **Alerting** | 4 / 25 | types et connecteurs tranchés ; **les options fines ne le sont pas** | créer une règle *Custom threshold* avec « Group alerts by » **et** l'alerte « no data », la laisser se déclencher, vérifier l'action `.index` |
| **Spaces et privilèges** | 8 / 26 | les 53 fonctionnalités sont relevées, mais aucun rôle n'a été éprouvé | créer `formateur` et `stagiaire`, se connecter avec chacun, vérifier qu'aucun sous-privilège n'est proposé |
| **Objets enregistrés et data views** | 13 / 19 | l'export fonctionne ; **l'import et la data view à ID imposé n'ont pas été exercés** | réimporter le ndjson dans un second Space, avec et sans `overwrite` ; créer une data view à identifiant imposé par API |
| **Terminologie** | 18 / 18 | quatre libellés relevés ; **le fr-FR de « data view » manque** (clé `dataViews.savedObjectName` absente) | relever les libellés sur l'écran réel et élargir la sonde aux clés du sélecteur de temps, du panneau Liens et de l'éditeur de drilldown |
| **Données et index** | 15 / 20 | aucun `index.mode` lu sur le lab | `GET logs-*-formation/_settings?filter_path=**.index.mode` et vérifier que le `_source` est **stocké**, non synthétique |
| **API Dashboards** | 22 / 24 | `POST`, l'export JSON de l'UI et l'API Visualizations n'ont pas été appelés | appeler `POST /api/dashboards` ; ouvrir le volet « Export JSON » et vérifier le badge d'aperçu (point E) |

### Contradictions à arbitrer

**A. Licence du drilldown Discover.** Le documentaliste « drilldowns » conclut **Basic**, en s'appuyant
sur le code du tag v9.5.3 où `getDiscoverDrilldown()` ne déclare aucun champ `license` ; le
documentaliste « passage vers Discover » conclut **non précisé**, en rappelant que les drilldowns ont
historiquement été une fonctionnalité d'abonnement. Les deux lisent la même documentation, qui se tait.
*Test qui tranche* : en Basic, ouvrir le menu d'un panneau Lens en mode Édition et vérifier si la tuile
*Ouvrir dans Discover* est cliquable ou grisée avec un message de licence. Si elle est grisée, le
pivot panneau → Discover sort de M3 et M4, ce qui change le capstone.

**B. Téléchargement CSV d'un panneau Lens : deux chemins, peut-être deux licences.** Le documentaliste
« export » classe *Download CSV* en « non précisé » et n'y voit aucun garde-fou ; le documentaliste
« Lens » a relevé dans le code 9.5 un garde `atLeastGold` sur l'intégration de partage
`downloadCsvLensShareProvider`, **qui ne concernerait que le menu *Share* du panneau**, pas le
*Download CSV* de l'inspecteur. *Test qui tranche* : en Basic, comparer les deux chemins — menu *Share*
du panneau, et *Inspect → Data → Download CSV* — et documenter lequel fonctionne. Enjeu réel : SPEC
§4.5 annonce « export CSV » comme disponible, et M4 s'appuie dessus en remplacement du PDF.

**C. Statut des variable controls dans Discover : `preview 9.2` ou `ga 9.2` ?** Deux pages officielles
de la même version se contredisent —
[explore-analyze/discover/try-esql.md:355-358](https://www.elastic.co/docs/explore-analyze/discover/try-esql)
dit `preview`,
[explore-analyze/query-filter/languages/esql-kibana.md:337](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana)
dit `ga`. *Test qui tranche* : créer un variable control dans Discover et regarder si l'UI affiche un
badge « Aperçu technique ». Le badge de l'interface fait foi.

**D. Modes `columnar` et `logsdb_columnar`.** `docs-content` les annonce en `preview 9.5`, tandis que la
branche **9.5** d'`elastic/elasticsearch` ne les liste pas dans la référence `index.mode` et n'a pas de
page `columnar`. *Test qui tranche* : `PUT _index_template/test` avec `"index.mode":"logsdb_columnar"` —
si Elasticsearch répond « unknown index mode », la référence 9.5 a raison. Sans effet sur le kit dans
les deux cas (aperçu technique).

### Divergences entre la documentation et le produit

**E. Badge « VERSION D'ÉVALUATION TECHNIQUE » dans le volet d'export JSON.** La documentation annonce
l'export JSON en GA 9.5 ; le code du tag v9.5.3 rend un badge *TECHNICAL PREVIEW* **sans condition**
dans l'en-tête du volet. *Test* : ouvrir le volet et chercher
`data-test-subj="dashboardExportJsonTechnicalPreviewBadge"`, **capture d'écran**. Si le badge est
visible, M5 doit le montrer et nuancer le discours « GA », sinon les stagiaires croiront à un défaut.

**F. Statut réel des annotations Lens.** La section porte un badge `stack: preview` **nu**, alors que les
annotations existent depuis longtemps et que la section voisine *Reference lines* n'a, elle, aucun
badge. Coquille de documentation probable. *Test* : regarder si l'UI affiche un badge d'aperçu technique
à côté d'*Annotations* dans le menu *Add layer*. Tant que ce n'est pas tranché, les annotations restent
hors du tronc commun de M2.

**G. Quelle interface du time filter s'affiche en 9.5.3 ?** La documentation présente par défaut la
variante redessinée, badgée `preview 9.5+` (*Presets*, *Calendar*, *Custom range*), tout en conservant
l'ancienne (*Quick select*, *Commonly used*) badgée `ga 9.0-9.4`. *Test* : ouvrir le sélecteur et
noter laquelle apparaît ; tester la saisie textuelle. **Bloquant pour les captures de M0.**

**H. Trois bascules ou deux dans l'éditeur de drilldown dashboard ?** La documentation n'en décrit que
deux ; le code 9.5 en déclare trois (la troisième étant *Open dashboard in new tab*). *Test* : compter
les cases et relever leur langue d'affichage (voir §15, point 20).

**I. Libellés doc contre produit.** `manage-panels.md` dit *View Discover session* là où le produit dit
*Open in Discover* ; `lens.md` dit *Explore data in Discover* là où le produit dit *Explore in
Discover*. *Règle* : ne jamais recopier un libellé d'interface depuis la prose de la documentation.

### Silences de la documentation

**J. Le comportement d'affichage des éléments verrouillés par la licence.** Masqués, ou visibles et
désactivés avec un badge d'abonnement ? La question se pose pour les types de règles, les connecteurs,
les tuiles de drilldown et les entrées du menu *Export*. **Ce n'est pas un détail** : c'est exactement
ce que le stagiaire aura sous les yeux, donc ce que les captures et les encadrés « Hors licence Basic »
doivent montrer. *Test* : capture d'écran de chaque écran concerné en Basic.

**K. Le message exact renvoyé quand la licence ne suffit pas.** Absent de `docs-content` (grep sans
résultat). Le relevé sur le lab n'y répond pas non plus : les deux routes de reporting sondées renvoient
un **404**, pas le 403 de licence décrit par le code. *Test* : relever mot pour mot le corps de la
réponse sur `printablePdfV2`, `pngV2` et `/internal/reporting/schedule/csv_searchsource`, **noter si
c'est un 403 de licence ou un 404 de route**, et si Kibana traduit le message en fr-FR.

**L. La planification d'exports est-elle vraiment hors Basic ?** Les prérequis documentés n'évoquent
que RAM, privilèges et connecteur de courriel — **jamais la licence**. Le code 9.5 et un test
d'intégration disent Gold. *Test* : le 403 ci-dessus. Si confirmé, c'est un **erratum de la
documentation Elastic**, à signaler au stagiaire comme tel.

**M. ~~Niveau de licence des règles de détection Elastic Security~~ — TRANCHÉ PAR LE LAB.**
`GET /api/alerting/rule_types` donne `minimum_license_required: basic` et `enabled_in_license: true`
pour les neuf types `siem.*` (requête personnalisée, requête enregistrée, EQL, ES\|QL, seuil,
nouveaux termes, correspondance d'indicateur, ML, notification héritée). Ils sont enseignables.

**N. Niveau de licence des fenêtres de maintenance** (« the appropriate subscription », sans palier
nommé, et la sonde ne les couvre pas). *Test* : présence de l'entrée dans Stack Management, puis
`GET kbn:/api/maintenance_window/_find`.

**O. TLS entre Kibana et Elasticsearch est-il un prérequis dur de l'alerting ?** Deux pages officielles
divergent : `alerting-setup.md` ne le cite pas parmi ses prérequis, la référence de configuration
Kibana en fait le prérequis numéro 2. *Test* : lab en `http://` avec sécurité activée — la règle se
crée-t-elle, s'exécute-t-elle, l'action part-elle ? **C'est ce test qui décidera si l'écart « HTTP sans
TLS toléré » de SPEC §4.1 est tenable.**

**P. Les formules Lens existent-elles en mode requête ES|QL ?** Constat **par absence** : la page ES|QL
ne contient aucune occurrence de « formula », mais nulle part la documentation ne l'interdit
explicitement. *Test* : basculer un panneau en ES|QL et regarder si l'option *Formula* est présente,
absente ou grisée. Ne rien affirmer avant.

**Q. Conditions non documentées du passage vers Discover. — SONDÉ, et le parcours avait tort.**
`outils/sonde_explorer_discover.py` construit quatre panneaux dans le Space « corriges », relève la
rangée d'actions de survol et les deux menus « … » (lecture et modification), puis clique l'action pour
voir si elle aboutit. Relevé sur 9.5.3 fr-FR :

| Panneau | Action offerte | Elle aboutit |
|---|---|---|
| un calque, aucun décalage | oui, au survol | oui — Discover s'ouvre, 378 364 documents |
| deux calques | **non** | — |
| un calque + décalage temporel `1d` | **non** | — |
| requête ES\|QL | oui, au survol | oui — Discover s'ouvre, 6 lignes |

Trois constats, dont deux démentent ce que le parcours enseignait :

1. **L'action n'est jamais dans le menu « … »**, ni en lecture ni en modification. C'est un bouton de la
   rangée qui apparaît au survol, `embeddablePanelAction-ACTION_OPEN_IN_DISCOVER`, libellé
   « Explorer dans Discover ». Le parcours disait « dans le menu du panneau » : c'était faux.
2. **Elle s'ouvre dans un nouvel onglet** — ce qui n'était dit nulle part, et qui change la consigne :
   « revenez » suppose de changer d'onglet, pas de cliquer « Précédent ».
3. Les deux refus annoncés — deux calques, décalage temporel — **sont confirmés**, et silencieux : ni
   bouton grisé, ni infobulle. La troisième condition annoncée, « une seule data view », n'a pas de cas
   propre : dans Lens une data view s'attache à un calque, donc deux data views supposent deux calques,
   et le cas est déjà couvert par le premier refus. Le parcours ne l'énonce plus séparément.

Reste non sondé : le privilège `discover_v2.show`. La sonde tourne avec le compte de fabrication ; le
vérifier demanderait un rôle taillé exprès, et aucun exercice n'en dépend. **NON EXÉCUTÉ**, pour cette
raison.

Effet de bord utile : le menu « … » d'un panneau en LECTURE ne compte que « Paramètres »,
« Télécharger CSV », « Copier dans le tableau de bord », « Ajouter au cas » (plus « Créer une règle
d'alerte » sur un panneau ES|QL). « Créer une exploration » n'apparaît qu'en MODIFICATION — le parcours
l'annonçait en lecture, sous un intitulé « Explorations » qui n'existe pas dans ce menu.

**R. `Enable accuracy mode`** (option sans badge, version minimale inconnue) et **S. les réglages
cluster `esql.query.result_truncation_*`** (snippet sans badge). *Tests* : présence de l'option dans
*Advanced* d'une dimension *Top values* ;
`GET /_cluster/settings?include_defaults=true&filter_path=**.esql.query.*`.

**T. Création de contrôles par l'API Dashboards.** La ligne « Controls: options list, range slider, time
slider, and ES|QL » ne porte aucun badge, et la mention « et ES|QL » est ambiguë : variable control
(preview) ou contrôle alimenté par requête (GA 9.5) ? *Test* : `POST` d'un panneau de contrôle puis
relecture par `GET` pour lire le nom exact du type dans le schéma JSON.

**U. `Share to space`.** L'ancre existe encore en tête de page et une page Security 9.x y renvoie, mais
la section a disparu de la page 9.x. *Test* : chercher l'entrée dans le menu d'actions d'une data view
et, si elle existe, vérifier `namespaces` dans
`GET /api/saved_objects/index-pattern/<id>`. Sinon, n'enseigner que *Copy to space*.

**V. Onglet *Permissions* d'un Space** (une phrase, aucun badge) ; **W. comportement de Fleet
space-aware en Basic** (la documentation dit « Enterprise requis » **et** « activé par défaut pour les
nouveaux déploiements 9.1+ », sans décrire ce qui se passe quand la licence ne suffit pas) ;
**X. champ *Index mode* dans l'assistant Index Templates de Kibana en Stack** (badgé `serverless`
uniquement) ; **Y. drilldowns développés par des tiers** (hors périmètre, mentionné pour
l'exhaustivité) ; **Z. le nom affiché « discover session » est-il traduit en fr-FR ?** (chaîne
littérale hors i18n dans le code 9.5.3).

### Le plus gros poste de travail de P1

**Tous les libellés d'interface en français.** La documentation Elastic n'existe qu'en anglais et n'est
pas prévue pour être localisée. Chaque tableau de ce document donne le **terme officiel anglais** pour
servir de clé de recherche ; **aucun libellé français du kit ne peut être écrit sans passage en lab**.
Le relevé a déjà fermé quatre cas — « Session Discover », « Tableaux de bord », « Section pliable »,
« Télécharger CSV » — sur 60 705 clés traduites ; tout le reste est à relever.
C'est une conséquence directe de `CLAUDE.md` : « Libellés d'UI cités : ceux de `kibana.locale`, relevés
dans le lab, jamais traduits de tête. »
