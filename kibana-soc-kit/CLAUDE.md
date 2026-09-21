# Kit de formation Kibana — règles permanentes

Kit de formation pratique à Kibana pour analystes SOC : lab conteneurisé hors ligne, données
synthétiques à scénarios cachés, guide interactif HTML autonome + PDF, fiche mémo, guide formateur,
évaluation, corrigés, suite de vérification, archive livrable.
- Quoi construire : `docs/SPEC.md` (relire les sections utiles avant chaque phase).
- Comment dérouler : `docs/ORCHESTRATION.md` (phases P0 → P8, critères de sortie, autonomie).
- Où on en est : `docs/JOURNAL.md` (état, décisions et raisons, écarts ouverts).
- Paramètres : `kit.config.yaml`, seule source de vérité (jamais de version, locale ou graine en dur).
- Reprise : si l'humain écrit « reprends », lire `docs/JOURNAL.md` puis poursuivre
  `docs/ORCHESTRATION.md` à la phase en cours.

## Contraintes non négociables
- IMPORTANT : données 100 % synthétiques. Aucune donnée, IP, nom d'hôte, nom d'index, configuration ou
  capture issue d'un système réel. IP externes RFC 5737, internes RFC 1918, domaines `.test`/`.example`.
- IMPORTANT : statuts honnêtes. Un contrôle non exécuté est NON EXÉCUTÉ (avec la raison), jamais PASSÉ.
  Interdit de modifier un test ou d'assouplir un critère pour obtenir un vert : corriger la cause, ou
  consigner l'écart dans le journal.
- Toute affirmation technique du guide est vérifiée dans la doc officielle de `stack.version`
  (9.x : elastic.co/docs, en respectant les badges « applies to » ; 8.x : elastic.co/guide/en/kibana/8.x),
  PUIS dans le lab. Une fonctionnalité absente du lab n'existe pas pour le parcours.
- Licence Basic uniquement : `xpack.license.self_generated.type: basic`, jamais de trial
  (le script start-local d'Elastic active un trial de 30 jours : ne pas l'utiliser).
- Runtime podman, lab lancé par `podman kube play` (natif, pas de compose), utilisable sur un réseau
  podman `--internal`. Kibana : `map.includeElasticMapsService: false`, télémétrie et newsfeed coupés.
- Livrable hors ligne : `dist/guide.html` sans aucune ressource externe ; images conteneur via
  `podman save` ; dépendances Python en wheels vendorisées ; `SHA256SUMS`.
- Aucun secret commité : mots de passe et clés générés à l'installation dans `.env` (gitignoré).
- Jamais de `sudo` exécuté par Claude : afficher la commande exacte et attendre l'humain.
- Contenu stagiaire en français, typographie française (« », espaces insécables). Libellés d'UI cités :
  ceux de `kibana.locale`, relevés dans le lab, jamais traduits de tête.
- Réglages par défaut de Kibana conservés : le stagiaire doit rencontrer les défauts de la production.

## Commandes (créées en P1, maintenues ensuite)
- `make lab-up` · `make lab-down` · `make lab-reset` (réancre les données sur maintenant)
- `make data` · `make data-epreuve` · `make captures` · `make guide` (HTML + PDF) · `make package`
- `make verif` = verif-lab, verif-donnees, verif-parcours, verif-corriges, verif-guide, verif-pdf,
  verif-package (chacune lançable seule)

## Définition de « fini »
- La cible `make verif-*` de la phase sort en 0 et sa sortie est affichée : une preuve, pas une affirmation.
- Aucune réponse attendue écrite à la main : elle vient du manifeste du générateur et est recalculée par
  requête sur le lab.
- Sous-agents `stagiaire-candide` puis `relecteur-expert` passés ; écarts bloquants et majeurs corrigés,
  mineurs consignés.

## Pièges transverses (ne pas les redécouvrir)
- Dashboards : `stack.version` ≥ 9.5 → API Dashboards (GA, tous niveaux de licence). Sinon, jamais de
  JSON Lens écrit de zéro : construire dans l'UI (Playwright) puis exporter en ndjson (API saved objects).
- Un export ndjson ne s'importe que dans la même version, une mineure plus récente ou la majeure suivante.
- Unique count (Lens) = agrégation cardinality approximative : toute réponse qui en dépend reste < 3000.
- Ne pas valider une requête KQL avec la fonction ES|QL `KQL()` : sa gestion de la casse sur les champs
  keyword a divergé de celle de Kibana selon les versions. Valider dans Discover (Playwright) + requête DSL.
- Une source muette ne produit aucun bucket : elle disparaît d'un « count par source » et ne déclenche
  jamais un seuil « count < 1 » groupé. Raisonner en « dernier événement vu par source » sur fenêtre longue.
- En Basic : connecteurs d'alerte Index et Server log seulement ; rapports PDF/PNG indisponibles (CSV oui).
- Playwright : `testIdAttribute: 'data-test-subj'` ; attendre `globalLoadingIndicator-hidden` avant capture ;
  `timezoneId: 'Europe/Paris'` ; locale = `kibana.locale`.
- Polices OFL à noms réservés : les embarquer telles que distribuées (pas de sous-ensemble ni conversion).

## Méthode
- Une phase à la fois ; relire CLAUDE.md, SPEC et JOURNAL en début de phase ; journal et commit en fin.
- Doute sur un comportement de Kibana : tester dans le lab, ne pas supposer.
- Commits atomiques en français, un par étape vérifiée. Bash passé à shellcheck, Python à ruff.
- En cas de compaction, conserver : phase en cours, dernières sorties de `make verif-*`, décisions,
  écarts ouverts, et la règle de relire CLAUDE.md, SPEC et JOURNAL avant de reprendre.
