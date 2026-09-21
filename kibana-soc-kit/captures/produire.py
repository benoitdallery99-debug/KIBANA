"""Produit les captures d'écran annotées — SPEC §7.2.

Règles tenues ici :
- viewport fixe, facteur d'échelle 2, locale et fuseau de kit.config.yaml,
  thème clair : le stagiaire doit voir ce que montre le guide ;
- les repères numérotés sont dessinés PAR SCRIPT à partir des boîtes
  englobantes des éléments visés par leur « data-test-subj » — jamais à la
  main, jamais retouchés ;
- les éléments variables (horodatages, durées de requête) sont masqués, sinon
  deux exécutions donneraient deux images différentes ;
- sortie en WebP, pour tenir dans les 20 Mo du guide.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf
from verif.e2e import kibana as K

DOSSIER = conf.RACINE / "captures"
SORTIE = DOSSIER / "images"

# Injecté avant la capture : masque ce qui change d'une exécution à l'autre.
MASQUAGE = """
() => {
  const variables = [
    '[data-test-subj="discoverQueryTotalHits"] .euiToolTipAnchor',
    '[data-test-subj="superDatePickerShowDatesButton"]',
    '[data-test-subj="lnsSuggestionPanel"]',
  ];
  for (const s of variables) {
    document.querySelectorAll(s).forEach(e => { e.style.visibility = 'hidden'; });
  }
  // Le curseur clignotant d'une zone de saisie apparaît au hasard des captures.
  const style = document.createElement('style');
  style.textContent = '*{caret-color:transparent!important}' +
                      '*{animation:none!important;transition:none!important}';
  document.head.appendChild(style);
}
"""

# Dessine les repères numérotés à partir des boîtes englobantes.
ANNOTATION = """
(reperes) => {
  const couche = document.createElement('div');
  couche.id = 'kit-reperes';
  Object.assign(couche.style, {
    position: 'fixed', inset: '0', zIndex: '2147483647', pointerEvents: 'none',
  });
  document.body.appendChild(couche);

  reperes.forEach((r, i) => {
    const cible = document.querySelector('[data-test-subj="' + r.cible + '"]');
    if (!cible) return;
    const b = cible.getBoundingClientRect();
    if (!b.width || !b.height) return;

    const cadre = document.createElement('div');
    Object.assign(cadre.style, {
      position: 'absolute',
      left: (b.left - 3) + 'px', top: (b.top - 3) + 'px',
      width: (b.width + 6) + 'px', height: (b.height + 6) + 'px',
      border: '2px solid #5b21b6', borderRadius: '3px',
    });
    couche.appendChild(cadre);

    const pastille = document.createElement('div');
    pastille.textContent = String(i + 1);
    Object.assign(pastille.style, {
      position: 'absolute',
      left: (b.left - 14) + 'px', top: (b.top - 14) + 'px',
      width: '24px', height: '24px', lineHeight: '24px',
      borderRadius: '50%', background: '#5b21b6', color: '#fff',
      font: '700 14px system-ui, sans-serif', textAlign: 'center',
    });
    couche.appendChild(pastille);
  });
  return couche.childElementCount;
}
"""


def main() -> int:
    plan = yaml.safe_load((DOSSIER / "plan.yaml").read_text(encoding="utf-8"))
    SORTIE.mkdir(parents=True, exist_ok=True)
    produites = []

    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        for capture in plan:
            K.aller_a(page, capture["chemin"])
            attendre = capture.get("attendre")
            if attendre:
                try:
                    page.wait_for_selector(
                        f'[data-test-subj="{attendre}"]', timeout=60_000
                    )
                except Exception as erreur:
                    print(f"  [ÉCHEC] {capture['id']} : « {attendre} » jamais apparu "
                          f"({type(erreur).__name__})")
                    continue
            page.wait_for_timeout(2_500)
            page.evaluate(MASQUAGE)
            dessines = page.evaluate(ANNOTATION, capture.get("reperes") or [])

            attendus = len(capture.get("reperes") or [])
            # Deux éléments par repère : le cadre et la pastille.
            if dessines != attendus * 2:
                print(f"  [ATTENTION] {capture['id']} : {dessines // 2} repère(s) "
                      f"dessiné(s) sur {attendus} — un sélecteur a changé ?")

            fichier = SORTIE / f"{capture['id']}.webp"
            page.screenshot(path=str(fichier), type="webp", quality=82)
            page.evaluate("() => document.getElementById('kit-reperes')?.remove()")
            produites.append(capture["id"])
            print(f"  [OK] {capture['id']:8s} {fichier.stat().st_size // 1024:4d} Ko  "
                  f"{capture['titre']}")

    manquantes = [c["id"] for c in plan if c["id"] not in produites]
    if manquantes:
        raise SystemExit(f"captures non produites : {manquantes}")
    print(f"{len(produites)} capture(s) dans {SORTIE.relative_to(conf.RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
