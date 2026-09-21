# Capacités qualifiées — Kibana 9.5.3, licence Basic

**Objet.** Ce document dit, capacité par capacité, ce qui a le droit d'exister dans le kit de formation.
Il couvre les capacités listées dans `docs/SPEC.md` §4.5. Il est la référence du rédacteur du parcours
en P3 : une capacité qui n'y figure pas en « oui » ne s'enseigne pas.

**Cible qualifiée** (`kit.config.yaml`, seule source de vérité) :

| Paramètre | Valeur |
|---|---|
| Version Elasticsearch / Kibana | **9.5.3** exactement |
| Licence | **Basic** auto-générée (`xpack.license.self_generated.type: basic`), jamais de trial |
| Locale Kibana | `fr-FR` |
| Vue de solution du Space | `classic` |

**Règle qui prime sur tout le reste** (`CLAUDE.md`) : *« Une fonctionnalité absente du lab n'existe pas
pour le parcours. »* La documentation officielle établit une présomption ; le lab tranche.

## Statut de ce document : P0, constats documentaires uniquement

La colonne « Confirmé en lab » de tous les tableaux est **vide** (`— (P1)`). Ce n'est pas un oubli,
c'est le statut honnête de la phase : à ce stade aucun test n'a été exécuté sur le lab. La phase P1
remplira cette colonne, ligne par ligne, avec **confirmé** ou **infirmé** — c'est un critère de sortie
de P1 (`docs/ORCHESTRATION.md`). Une ligne marquée « oui » ici et infirmée en P1 sort du parcours sans
discussion.

En conséquence, tout ce qui suit se lit comme : *« la documentation officielle de la ligne 9.x affirme
ceci, avec cette citation et ce badge de version »*, et non comme : *« ceci fonctionne sur notre lab »*.

---

## Comment ces constats ont été établis

> **Source documentaire.** `www.elastic.co` et `docker.elastic.co` sont bloqués par la politique
> d'egress du poste de fabrication (403 au CONNECT ; écart **E1** du journal, contourné, pas résolu).
> La documentation officielle Elastic 9.x a donc été lue **dans son dépôt source**,
> `github.com/elastic/docs-content`, qui est l'amont dont `elastic.co/docs` est engendré — une source
> officielle, pas un succédané. Clone local au commit `e74a5db` (21/09/2026).
> Les références qui ne vivent pas dans ce dépôt (référence ES|QL, agrégations, réglages Kibana,
> spécification OpenAPI de l'API Dashboards) ont été lues sur les branches **9.5** des dépôts
> `elastic/elasticsearch` et `elastic/kibana` via `raw.githubusercontent.com`. Chaque ligne concernée le
> signale explicitement par la mention « hors docs-content ».
>
> **Règle des badges `applies_to`.** Chaque page porte un frontmatter YAML `applies_to:` et peut porter
> des badges en ligne sur une section ou une option précise. C'est le badge **le plus proche de
> l'affirmation citée** qui fait foi, jamais seulement celui de la page. Lecture retenue :
> `ga 9.5+` → disponible en 9.5.3 ; `ga 9.6+` → **absent** en 9.5.3 ; `preview 9.5` → présent mais en
> aperçu technique, signalé comme tel ; `=9.4` → cette version seulement ; `ga 9.0-9.3` → décrit un
> comportement **antérieur**, à ne pas recopier. La documentation 9.x est **cumulative** : une seule
> édition décrit 9.0 à 9.6, donc une page lue sans son badge décrit souvent une version que le lab
> n'a pas.
>
> **Règle de licence.** Le kit n'enseigne que ce qui existe en Basic. Pour chaque capacité, la mention
> de niveau d'abonnement a été cherchée explicitement. Constat massif et à assumer : **la documentation
> est presque toujours muette sur le niveau d'abonnement**. Elle renvoie à `elastic.co/subscriptions`,
> page justement inaccessible. Quand elle se tait, la colonne « Basic » porte **« non précisé »** et non
> « oui » : aucune déduction n'a été transformée en affirmation. À noter que la documentation *sait*
> marquer ce qui est payant quand ça l'est — `sharing.md:74` écrit « PDF and PNG reports are a
> subscription feature » — ce qui fait de son silence un indice sérieux, mais un indice seulement.
>
> **URL canoniques.** Le chemin du fichier donne l'URL : `explore-analyze/dashboards/sharing.md` →
> `https://www.elastic.co/docs/explore-analyze/dashboards/sharing`. Pour les fichiers lus dans
> `elastic/elasticsearch`, le préfixe `docs/` saute. Les URL fournies n'ont **pas pu être ouvertes**
> pour vérification (egress bloqué) : elles sont reconstruites par cette règle, utiles au lecteur du
> kit qui, lui, n'a pas notre contrainte réseau. Le libellé de chaque lien est le chemin du fichier
> réellement lu, avec ses numéros de ligne.
>
> **Ce que ce document ne prouve pas.** Aucun libellé d'interface en français n'est établi ici : la
> documentation Elastic n'existe qu'en anglais et n'est pas prévue pour être localisée
> (`contribute-docs/how-to/seo.md:388`). Les seuls libellés fr-FR officiels sont ceux du fichier de
> traduction livré avec Kibana 9.5.3 (60 705 clés) ; ils sont cités en note quand ils sont connus, mais
> **tout libellé cité dans le guide doit être relevé dans le lab**, conformément à `CLAUDE.md`.

---

## 1. API Dashboards et dashboards-as-code

Famille la mieux documentée du lot, et la plus neuve : **tout y est GA exactement en 9.5**, donc absent
de 9.4 et antérieur. Aucune page ne mentionne de niveau d'abonnement.

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| API Dashboards (REST), statut général | Dashboards API | oui | non précisé | 9.5 | [explore-analyze/dashboards/create-dashboards-programmatically.md:4-6](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboards-programmatically) | — (P1) |
| `POST /api/dashboards` — créer, ID généré | Create a dashboard | oui | non précisé | 9.5 | [explore-analyze/kibana-data-exploration-learning-tutorial.md:723-726](https://www.elastic.co/docs/explore-analyze/kibana-data-exploration-learning-tutorial) | — (P1) |
| `PUT /api/dashboards/{id}` — upsert idempotent | Upsert a dashboard | oui | non précisé | 9.5 | [explore-analyze/dashboards/manage-dashboards-as-code.md:61](https://www.elastic.co/docs/explore-analyze/dashboards/manage-dashboards-as-code) | — (P1) |
| `GET /api/dashboards` — lister et rechercher | Search dashboards | oui | non précisé | 9.5 | hors docs-content : [dashboards-api-spec/openapi/kibana-openapi.yaml:13226-13227](https://elastic.github.io/dashboards-api-spec/dashboards) | — (P1) |
| `GET /api/dashboards/{id}` — état complet | Get a dashboard | oui | non précisé | 9.5 | hors docs-content : [dashboards-api-spec/openapi/kibana-openapi.yaml:14296](https://elastic.github.io/dashboards-api-spec/dashboards) | — (P1) |
| `DELETE /api/dashboards/{id}` | Delete a dashboard | oui | non précisé | 9.5 | hors docs-content : [dashboards-api-spec/openapi/kibana-openapi.yaml:14252-14262](https://elastic.github.io/dashboards-api-spec/dashboards) | — (P1) |
| En-tête `kbn-xsrf: true` obligatoire en écriture | CSRF protection header | oui | s. o. | 9.5 | hors docs-content : [dashboards-api-spec/openapi/kibana-openapi.yaml:114-116](https://elastic.github.io/dashboards-api-spec/dashboards) | — (P1) |
| Préfixe d'espace `s/{space_id}/` dans l'URL | Spaces path prefix | oui | non précisé | non lié à 9.5 | [api/kibana/kibana-api-overview.md:9-15](https://www.elastic.co/docs/api/kibana/kibana-api-overview) | — (P1) |
| Export JSON d'un dashboard depuis l'UI | Export JSON | oui | non précisé | 9.5 | [explore-analyze/dashboards/sharing.md:107-117](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | — (P1) |
| Badge « VERSION D'ÉVALUATION TECHNIQUE » dans le volet d'export | TECHNICAL PREVIEW badge | **indéterminé** | s. o. | indéterminé | hors docs-content : `elastic/kibana` v9.5.3, `src/platform/plugins/shared/dashboard/public/share/export_json_flyout.tsx:89-99` | — (P1) |
| Actions du volet : copier, télécharger, ouvrir dans la console | Copy / Download JSON / Open in Console | oui | non précisé | 9.5 | [explore-analyze/dashboards/sharing.md:113-117](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | — (P1) |
| Avertissement « propriétés non prises en charge supprimées » | Unsupported properties were removed | oui | non précisé | 9.5 | [explore-analyze/dashboards/sharing.md:112](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | — (P1) |
| Export JSON d'un **panneau isolé** | Export a panel as JSON | **non** | s. o. | 9.6 (preview) | [explore-analyze/dashboards/sharing.md:139-143](https://www.elastic.co/docs/explore-analyze/dashboards/sharing) | — (P1) |
| Export NDJSON des objets enregistrés | Export saved objects | oui | non précisé | antérieure à 9.0 | [explore-analyze/find-and-organize/saved-objects.md:80-87](https://www.elastic.co/docs/explore-analyze/find-and-organize/saved-objects) | — (P1) |
| Import d'un dashboard : JSON (API) ou NDJSON (saved objects) | Import a dashboard | oui | non précisé | 9.5 (JSON) / non borné (NDJSON) | [explore-analyze/dashboards/import-dashboards.md:17-18](https://www.elastic.co/docs/explore-analyze/dashboards/import-dashboards) | — (P1) |
| API Visualizations (bibliothèque) | Visualizations API | oui | non précisé | 9.5 | [explore-analyze/dashboards/create-dashboards-programmatically.md:59-73](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboards-programmatically) | — (P1) |
| API Tags | Tags API | **preview** | non précisé | 9.5 | hors docs-content : [dashboards-api-spec/openapi/kibana-openapi.yaml:69687](https://elastic.github.io/dashboards-api-spec/tags) | — (P1) |
| API Links et API Markdowns | Links API / Markdowns API | **non** | s. o. | 9.6 | hors docs-content : [dashboards-api-spec/openapi/kibana-openapi.yaml:45903, :49686](https://elastic.github.io/dashboards-api-spec/links) | — (P1) |
| Paramètres `tag_names` / `excluded_tag_names` de `GET /api/dashboards` | — | **non** | s. o. | 9.6 | hors docs-content : [dashboards-api-spec/openapi/kibana-openapi.yaml:13288, :13298](https://elastic.github.io/dashboards-api-spec/dashboards) | — (P1) |
| Types de panneaux acceptés en écriture | Supported panel types | oui | non précisé | 9.5 | [explore-analyze/dashboards/create-dashboards-programmatically.md:40-53](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboards-programmatically) | — (P1) |
| Types refusés : `map`, `legacy_vis`, `alerts_table` | Panel types without a defined schema | **non** (400 en écriture) | s. o. | 9.5 | [explore-analyze/dashboards/create-dashboards-programmatically.md:51](https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboards-programmatically) | — (P1) |
| Limites de panneaux (1 000 éléments, 1 000 par section, 100 contrôles épinglés) | Panel limits | oui | non précisé | 9.4 | [explore-analyze/dashboards/arrange-panels.md:89-103](https://www.elastic.co/docs/explore-analyze/dashboards/arrange-panels) | — (P1) |
| Grille de positionnement à 48 colonnes | 48-column grid | oui | s. o. | 9.5 | [explore-analyze/dashboards/arrange-panels.md#dashboard-grid-layout](https://www.elastic.co/docs/explore-analyze/dashboards/arrange-panels) | — (P1) |
| Portabilité : ES\|QL en ligne, data view à ID choisi | Keep references portable | oui | non précisé | 9.5 | [explore-analyze/dashboards/manage-dashboards-as-code.md:38-62](https://www.elastic.co/docs/explore-analyze/dashboards/manage-dashboards-as-code) | — (P1) |
| Provider Terraform `elasticstack_kibana_dashboard` | Elastic Stack Terraform provider | **preview** | non précisé | indéterminé | [explore-analyze/dashboards/manage-dashboards-as-code.md:66-85](https://www.elastic.co/docs/explore-analyze/dashboards/manage-dashboards-as-code) | — (P1) |
| Flux as-code en quatre étapes | Export / Store / Review / Deploy | oui | non précisé | 9.5 | [explore-analyze/dashboards/manage-dashboards-as-code.md:23-34](https://www.elastic.co/docs/explore-analyze/dashboards/manage-dashboards-as-code) | — (P1) |

### Ce qu'il faut tester en P1

1. **Licence puis accès (test décisif de toute la famille).** `GET /_license` doit renvoyer
   `type: basic`, `status: active`. Puis :
   `curl -u elastic:<mdp> -X GET 'http://kibana:5601/api/dashboards?per_page=5' -H 'kbn-xsrf: true'`
   → attendu **200**. Puis `POST /api/dashboards` avec le corps minimal `{"title":"TEST SOC"}` →
   attendu **201** avec un `id` généré. Si les deux passent, la question de la licence est réglée pour
   l'ensemble du module M5.
2. **Idempotence du `PUT`.** `PUT /api/dashboards/soc-demo-001` avec le JSON exporté → 201 la première
   fois, 200 ensuite, ID inchangé. Rejouer le même `PUT` **en retirant un panneau du corps** et
   vérifier que le panneau disparaît : le remplacement est total, il n'existe pas de `PATCH`.
3. **En-têtes.** (a) `POST` sans `kbn-xsrf` → attendu 400. (b) `POST` **sans** `elastic-api-version` →
   vérifier que la requête passe. (c) `POST` **avec** `elastic-api-version: 2023-10-31` → vérifier
   qu'elle passe aussi. Relever l'en-tête `elastic-api-version` présent dans la *réponse*.
4. **Types de panneaux refusés (P1 prioritaire).** `POST /api/dashboards` avec un panneau de type `map`
   → attendu **400**. Puis, sur un dashboard contenant une carte, `GET /api/dashboards/{id}` : vérifier
   que le panneau est absent de `data.panels` et **relever le nom exact du champ d'avertissements**.
5. **Badge « VERSION D'ÉVALUATION TECHNIQUE » (P1 prioritaire).** Ouvrir *Exporter → Exporter JSON* et
   regarder si un badge est affiché à côté du titre du volet
   (sélecteur de test `data-test-subj="dashboardExportJsonTechnicalPreviewBadge"`). **Capture d'écran.**
6. **Chemin de clics et libellés fr-FR.** Relever, en locale `fr-FR` et vue `classic` : l'entrée de menu
   *Exporter → Exporter JSON*, le titre du volet, les trois boutons, le libellé de l'avertissement.
7. **« Ouvrir dans la console ».** Relever la requête prépopulée exacte (attendu :
   `POST kbn:/api/dashboards`, donc une **création** sans préfixe d'espace).
8. **Espace.** Créer l'espace `formation` puis `POST /s/formation/api/dashboards` et vérifier que le
   dashboard n'apparaît **pas** dans l'espace `default`.
9. **Constats négatifs à confirmer.** `GET /api/links` → attendu **404**. Menu contextuel d'un panneau
   Lens → absence d'une entrée *Exporter JSON*. `GET /api/dashboards?tag_names=soc` → le paramètre ne
   doit pas être reconnu.
10. **JSON contre NDJSON.** Exporter le *même* dashboard par les deux voies, comparer les deux fichiers
    côte à côte et compter les objets embarqués par le NDJSON.

## 2. ES|QL dans Discover et dans Lens

Le cœur d'ES|QL est **GA sans borne de version** : la page Discover et la page des visualisations
portent toutes deux `stack: ga` sans numéro, donc GA sur toute la ligne 9.x. Aucune page n'indique de
niveau d'abonnement pour le moteur, l'éditeur ou les visualisations ; en revanche la documentation
**exclut explicitement trois sous-capacités** en les marquant Enterprise. Dans les cellules ci-dessous,
`ES\|QL` se lit « ES|QL » (la barre est échappée pour le tableau).

| Capacité | Terme officiel (en) | 9.5.3 | Basic | Version min | Source | Confirmé en lab |
|---|---|---|---|---|---|---|
| Mode ES\|QL dans Discover | ES\|QL mode in Discover | oui | non précisé | 9.0 (`ga` sans borne) | [explore-analyze/discover/try-esql.md:4-6, :14](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Réglage `enableESQL` — actif par défaut, désactivable | enableESQL advanced setting | oui | non précisé | 9.0 | [explore-analyze/discover/try-esql.md:18](https://www.elastic.co/docs/explore-analyze/discover/try-esql) + hors docs-content : `elastic/kibana`@9.5 `docs/reference/advanced-settings-space.yml:538-552` | — (P1) |
| Réglage nommé `esql:enabled` | — | **n'existe pas** | s. o. | s. o. | recherche exhaustive : 0 occurrence dans docs-content ; hors docs-content : `advanced-settings-space.yml` ne connaît que `enableESQL` | — (P1) |
| `LIMIT` implicite à 1 000 lignes, plafond dur à 10 000 | Result set size limit | oui | non précisé | 9.0 | hors docs-content : [elasticsearch@9.5 docs/reference/query-languages/esql/limitations.md:14](https://www.elastic.co/docs/reference/query-languages/esql/limitations) | — (P1) |
| Réglages cluster `esql.query.result_truncation_*` | result_truncation_default_size / _max_size | **indéterminé** | non précisé | indéterminé (aucun badge) | hors docs-content : [elasticsearch@9.5 .../_snippets/common/result-set-size-limitation.md:30-33](https://www.elastic.co/docs/reference/query-languages/esql/limitations) | — (P1) |
| Limites d'affichage Discover : 10 000 lignes, **50 colonnes**, CSV 10 000 lignes | Discover ES\|QL results table limitations | oui | non précisé | 9.0 | [explore-analyze/discover/try-esql.md:166-171](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Pas d'UI de filtres en mode ES\|QL ; filtres actifs convertis en `WHERE` | No data filtering UI | oui | non précisé | 9.4 (conversion) | [explore-analyze/discover/try-esql.md:171-173, :42-43](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Tri par en-tête de colonne = tri **côté client** sur les lignes déjà remontées | Sort query results (client-side) | oui | non précisé | 9.0 | [explore-analyze/discover/try-esql.md:176-184](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Fonction `KQL()` dans ES\|QL | ES\|QL KQL function | oui | non précisé | 9.1 (GA ; preview 9.0) | hors docs-content : [elasticsearch@9.5 .../search-functions/kql.md:1-10](https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/search-functions/kql) | — (P1) |
| `KQL()` sensible à la casse sur keyword — `case_insensitive` vaut `false` par défaut | KQL named parameter case_insensitive | oui | non précisé | 9.3 (paramètre) | hors docs-content : [elasticsearch@9.5 .../functionNamedParams/kql.md](https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/search-functions/kql) | — (P1) |
| KQL sur keyword : correspondance exacte, casse et ponctuation comprises | KQL exact match on keyword fields | oui | non précisé | 9.0 | [explore-analyze/query-filter/languages/kql.md:66](https://www.elastic.co/docs/explore-analyze/query-filter/languages/kql) | — (P1) |
| Sans `MATCH`/`QSTR`/`KQL`, un champ `text` se comporte comme un `keyword` | Full-text search limitations | oui | non précisé | 9.0 | hors docs-content : [elasticsearch@9.5 docs/reference/query-languages/esql/limitations.md:190-194](https://www.elastic.co/docs/reference/query-languages/esql/limitations) | — (P1) |
| Barre de recherche KQL de l'éditeur (génère `WHERE KQL()`) | Build ES\|QL queries from KQL syntax | **preview** | non précisé | 9.3 | [explore-analyze/query-filter/languages/esql-kibana.md:126-147](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — (P1) |
| Visualisations Lens construites à partir d'une requête ES\|QL | Visualization (query) / ES\|QL panel | oui | non précisé | 9.0 | [explore-analyze/visualize/esorql.md:5-7, :46](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — (P1) |
| Prototypage depuis Discover : édition du graphe et enregistrement vers un dashboard | Edit and add from Discover | oui | non précisé | 9.0 | [explore-analyze/visualize/esorql.md:29-33](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — (P1) |
| Persistance de la configuration du graphe après modification de la requête | Chart configuration persistence | oui | non précisé | 9.1 | [explore-analyze/visualize/esorql.md:103-114](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — (P1) |
| Breakdown multi-champs sur graphes ES\|QL | Break down a chart by multiple fields | oui | non précisé | 9.4 | [explore-analyze/visualize/esorql.md:81-101](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — (P1) |
| Ignorer les filtres globaux du dashboard sur une couche ES\|QL | Use global filters toggle | oui | non précisé | 9.5 | [explore-analyze/visualize/esorql.md:182-192](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — (P1) |
| Drilldowns depuis un panneau ES\|QL (dashboard, URL, Discover) | Add drilldowns to an ES\|QL visualization | oui | voir famille 5 | 9.4 (9.5 pour Discover) | [explore-analyze/visualize/esorql.md:168-180](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — (P1) |
| Contrôles de variables ES\|QL (Discover et dashboards) | Variable controls | **preview** | non précisé | 9.0 / 9.2 | [explore-analyze/visualize/add-variable-controls.md:5-7](https://www.elastic.co/docs/explore-analyze/visualize/add-variable-controls) | — (P1) |
| Mode rapide / approximation des `STATS` | Fast mode / SET approximation | **preview** | **non — Enterprise** | 9.4 / 9.5 | [explore-analyze/query-filter/languages/esql-kibana.md:464-546](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — (P1) |
| Assistance IA dans l'éditeur (langage naturel, « Fix with AI ») | Write and fix queries with AI | **preview** | **non — Enterprise + connecteur LLM** | 9.5 | [explore-analyze/query-filter/languages/esql-kibana.md:150-241](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — (P1) |
| ES\|QL en recherche multi-clusters | ES\|QL cross-cluster search | oui | **non — Enterprise** | non borné | hors docs-content : [elasticsearch@9.5 .../esql-cross-clusters.md:24](https://www.elastic.co/docs/reference/query-languages/esql/esql-cross-clusters) | — (P1) |
| Historique des requêtes et requêtes favorites | Query history / Starred queries | oui | non précisé | 9.2 (50 Ko, recherche) | [explore-analyze/query-filter/languages/esql-kibana.md:357-385](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — (P1) |
| Navigateurs d'index et de champs dans l'éditeur | Data source browser / Fields browser | oui | non précisé | 9.4 | [explore-analyze/discover/try-esql.md:99-120](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Statistiques de requête, `prettify`, avertissements, raccourcis | Query statistics / Prettify / Warnings | oui | non précisé | 9.4 | [explore-analyze/query-filter/languages/esql-kibana.md:72-123](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — (P1) |
| Directive `SET` et fuseau horaire via `dateFormat:tz` | SET directive / Timezone handling | oui | non précisé | 9.4 | [explore-analyze/query-filter/languages/esql-kibana.md:314-328, :388-409](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql-kibana) | — (P1) |
| Requête ES\|QL de départ configurable (`discover:defaultEsqlQuery`) | Default ES\|QL query setting | **non** | s. o. | 9.6 | [explore-analyze/discover/try-esql.md:45](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Affichage groupé des résultats `STATS BY` (cascade) et sparklines | View grouped results / SPARKLINE | **preview** | non précisé | 9.4 / 9.5 | [explore-analyze/discover/try-esql.md:395-468](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Création et édition d'index de correspondance (`LOOKUP JOIN`) depuis l'éditeur | Create and edit lookup indices | **preview** | non précisé | 9.2 | [explore-analyze/discover/try-esql.md:209-352](https://www.elastic.co/docs/explore-analyze/discover/try-esql) | — (P1) |
| Résultats partiels après expiration ou annulation | Partial results / Cancel a running query | oui | non précisé | 9.1 / 9.3 | [explore-analyze/discover/discover-get-started.md:303-328](https://www.elastic.co/docs/explore-analyze/discover/discover-get-started) | — (P1) |
| Créer une règle d'alerte depuis une visualisation ES\|QL | Create an alert from your ES\|QL visualization | oui | non précisé | 9.1 | [explore-analyze/visualize/esorql.md:194-216](https://www.elastic.co/docs/explore-analyze/visualize/esorql) | — (P1) |

### Ce qu'il faut tester en P1

1. **Test de licence unique pour toute la famille.** `GET /_license` (attendu `basic`/`active`), puis
   trois appels `POST /_query` qui tranchent une dizaine de lignes d'un coup :
   `{"query":"FROM logs-*-formation | LIMIT 10"}` (attendu 200),
   `{"query":"SET approximation=true; FROM logs-*-formation | STATS c=COUNT(*) BY host.name"}`
   (attendu : **erreur de licence**, relever le message exact),
   `{"query":"FROM remote:logs-* | LIMIT 1"}` (attendu : erreur, relever le symptôme).
2. **Limites de sortie.** `POST /_query {"query":"FROM logs-*-formation | LIMIT 20000"}` → compter les
   lignes (attendu **10 000**). Sans `LIMIT` → attendu **1 000**.
   `GET /_cluster/settings?include_defaults=true&flat_settings=true&filter_path=**.esql.query.*` pour
   établir si les deux réglages de troncature existent et avec quelles valeurs.
3. **Casse de `KQL()` (P1 prioritaire — pilier de M1).** Indexer deux documents dont un champ keyword
   vaut `Admin` et `admin`, puis comparer
   `FROM test | WHERE KQL("u: admin")` (attendu **1** résultat) et
   `FROM test | WHERE KQL("u: admin", {"case_insensitive": true})` (attendu **2**).
   Vérifier au passage que la syntaxe des paramètres nommés (introduite en 9.3) est acceptée.
4. **Champ `text` contre `keyword`.** Sur les données du lab, comparer `WHERE message == "GET"`,
   `WHERE KQL("message: GET")` et `WHERE MATCH(message, "GET")`, après avoir lu le mapping réel avec
   `GET logs-*-formation/_mapping`.
5. **Réglage `enableESQL`.** Stack Management → Advanced Settings → chercher `esql` : relever la **liste
   exhaustive** des clés en 9.5.3 et confirmer l'absence de `esql:enabled` et de `defaultEsqlQuery`.
   Désactiver `enableESQL`, recharger Discover, constater la disparition du point d'entrée et vérifier
   qu'une session ES|QL enregistrée reste ouvrable.
6. **Colonnes et CSV.** `FROM logs-*-formation | KEEP * | LIMIT 10000` : compter les colonnes affichées
   (attendu **50 au maximum**), puis exporter en CSV et vérifier la troncature à 10 000 lignes.
7. **Piège du tri.** Exécuter une requête sans `SORT`, trier une colonne numérique par l'UI, noter le
   maximum affiché, puis comparer à `STATS MAX(...)`. C'est l'exercice de M2.
8. **Résultats partiels.** Lancer une requête lourde sur une plage large, l'annuler, vérifier que des
   résultats partiels s'affichent **avec un indicateur explicite**, et relever la valeur de
   `search:timeout`.
9. **Bascule classic → ES|QL.** Poser deux filtres (un simple, un DSL personnalisé), basculer en ES|QL,
   relever ce qui est traduit en `WHERE` et **quel avertissement fr-FR** signale ce qui est abandonné.
10. **Constats négatifs d'interface en Basic.** Sans connecteur LLM : absence du lien « Fix with AI »,
    absence du mode « Natural language » dans la barre `ctrl+k`, `ctrl+J` sans effet. Vérifier aussi si
    le bouton éclair « Fast mode » est visible malgré l'indisponibilité. **Captures d'écran.**
11. **Libellés fr-FR à relever** (aucune source documentaire n'existe) : point d'entrée ES|QL dans
    Discover, onglet « Results », bouton d'historique, pied de l'éditeur (statistiques), panneau
    d'avertissements, libellé du panneau ES|QL dans *Ajouter un panneau*.
