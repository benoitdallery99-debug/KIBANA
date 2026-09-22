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

import datetime
import json
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
  //
  // ARTEFACT MESURÉ : la rangée d'actions rapides d'un panneau — filtre,
  // exploration, inspection, agrandissement, menu — restait peinte en haut à
  // droite d'un panneau sur M3-C1 et M4-C1, parce que le pointeur de
  // Playwright s'était arrêté dessus. Le stagiaire voyait donc une barre
  // d'outils qu'il n'obtiendrait qu'en survolant, sans que rien ne l'explique,
  // et sur un panneau choisi au hasard. On la neutralise pour toutes les
  // captures ; celles qui doivent la montrer la montreront par un geste
  // déclaré, pas par un accident de pointeur.
  const style = document.createElement('style');
  style.textContent = '*{caret-color:transparent!important}' +
                      '*{animation:none!important;transition:none!important}' +
                      // NE PAS viser le conteneur « embPanel__hoverActions » :
                      // en 9.5 il ENVELOPPE le panneau, et le masquer efface
                      // l'écran entier. Constaté : M3-C1 rendu vide, M4-C1
                      // refusée faute de « embeddablePanel » visible. On ne
                      // masque que les boutons.
                      '[data-test-subj^="embeddablePanelAction-"],' +
                      '[data-test-subj^="hover-actions-"],' +
                      '[data-test-subj="embeddablePanelToggleMenuIcon"]' +
                      '{opacity:0!important;visibility:hidden!important}';
  document.head.appendChild(style);
}
"""

# Dessine les repères numérotés à partir des boîtes englobantes.
#
# La pastille se pose AU-DESSUS du cadre, jamais à cheval sur son coin :
# à cheval, elle masque le début de ce qu'elle désigne — le premier chiffre
# du compteur de M1-C1, par exemple. Et elle est bornée dans la fenêtre :
# posée sur un élément collé au bord gauche (la liste des champs), elle en
# sortait et son numéro devenait illisible.
ANNOTATION = """
(reperes) => {
  const COTE = 24;   // diamètre de la pastille
  const MARGE = 2;   // dégagement minimal au bord de la capture

  const couche = document.createElement('div');
  couche.id = 'kit-reperes';
  Object.assign(couche.style, {
    position: 'fixed', inset: '0', zIndex: '2147483647', pointerEvents: 'none',
  });
  document.body.appendChild(couche);

  const introuvables = [];
  const mal_placees = [];
  const serrees = [];
  let dessines = 0;

  reperes.forEach((r, i) => {
    const cible = document.querySelector('[data-test-subj="' + r.cible + '"]');
    if (!cible) { introuvables.push(r.cible); return; }
    const b = cible.getBoundingClientRect();
    if (!b.width || !b.height) { introuvables.push(r.cible); return; }

    const cadre = document.createElement('div');
    Object.assign(cadre.style, {
      position: 'absolute',
      left: (b.left - 3) + 'px', top: (b.top - 3) + 'px',
      width: (b.width + 6) + 'px', height: (b.height + 6) + 'px',
      border: '2px solid #5b21b6', borderRadius: '3px',
    });
    couche.appendChild(cadre);

    // Quatre places candidates, essayées dans cet ordre : au-dessus du cadre,
    // à sa gauche, à sa droite, sous lui. La première qui ne recouvre RIEN
    // gagne.
    //
    // PIÈGE MESURÉ : le code ne vérifiait que le recouvrement de la CIBLE.
    // Sur M4-C1, la pastille du premier titre de panneau, bornée à la marge
    // gauche, se posait sur la barre de filtres — donc sur le bouton
    // « Ajouter un filtre » et son menu. Elle ne recouvrait pas sa cible : le
    // contrôle passait, et l'image montrait un rond violet au milieu d'une
    // barre d'outils.
    // On ne regarde que l'élément du DESSUS à chaque point, et on ne le compte
    // que s'il porte lui-même de l'encre : du texte en propre, ou un contrôle.
    // Remonter la pile des ancêtres déclarait tout occupé — le conteneur d'un
    // panneau « contient du texte » même là où le pixel est blanc.
    const encre = (e) => {
      if (!e || couche.contains(e) ||
          e === document.body || e === document.documentElement) return false;
      if (['BUTTON', 'INPUT', 'IMG', 'svg', 'path', 'CANVAS'].includes(e.tagName)) {
        return true;
      }
      for (const n of e.childNodes) {
        if (n.nodeType === 3 && n.nodeValue.trim()) return true;
      }
      return false;
    };
    const occupe = (x, y) => {
      const points = [
        [x + 3, y + 3], [x + COTE - 3, y + 3],
        [x + 3, y + COTE - 3], [x + COTE - 3, y + COTE - 3],
        [x + COTE / 2, y + COTE / 2],
      ];
      return points.some(([px, py]) => {
        const pile = document.elementsFromPoint(px, py)
          .filter(e => !couche.contains(e));
        return encre(pile[0]);
      });
    };

    const places = [
      [b.left - 3, b.top - 5 - COTE],              // au-dessus
      [b.left - 5 - COTE, b.top - 3],              // à gauche
      [b.right + 5, b.top - 3],                    // à droite
      [b.left - 3, b.bottom + 5],                  // dessous
    ];
    // Dernier recours avant le repli : DANS la cible, calée à son extrémité
    // droite. Un titre de panneau est une boîte large dont le texte n'occupe
    // que la gauche : la pastille y tient sans rien masquer, là où les quatre
    // places extérieures butent sur la barre de filtres ou sur le panneau
    // voisin. C'est ce qui posait la pastille 1 de M3-C1 et M4-C1 sur le
    // bouton « Ajouter un filtre ».
    if (b.width > 3 * COTE && b.height >= COTE) {
      places.push([b.right - COTE - 4, b.top + (b.height - COTE) / 2]);
    }
    const tient = ([cx, cy]) =>
      cx >= MARGE && cy >= MARGE &&
      cx + COTE <= window.innerWidth - MARGE &&
      cy + COTE <= window.innerHeight - MARGE;

    const dans_le_cadre = places.filter(tient);
    if (!dans_le_cadre.length) {
      mal_placees.push({numero: i + 1, cible: r.cible, sort: true,
                        recouvre: false});
      return;
    }
    // La première place LIBRE ; à défaut, la première qui tient dans le cadre.
    // Sur une interface dense — la liste des champs de Discover, collée au
    // bord — les quatre places portent de l'encre : on pose quand même, et on
    // le dit, plutôt que de refuser la capture.
    let x = null, y = null;
    for (const [cx, cy] of dans_le_cadre) {
      if (!occupe(cx, cy)) { x = cx; y = cy; break; }
    }
    if (x === null) {
      [x, y] = dans_le_cadre[0];
      serrees.push({numero: i + 1, cible: r.cible});
    }

    const pastille = document.createElement('div');
    pastille.textContent = String(i + 1);
    Object.assign(pastille.style, {
      position: 'absolute',
      left: x + 'px', top: y + 'px',
      width: COTE + 'px', height: COTE + 'px', lineHeight: COTE + 'px',
      borderRadius: '50%', background: '#5b21b6', color: '#fff',
      font: '700 14px system-ui, sans-serif', textAlign: 'center',
    });
    couche.appendChild(pastille);
    dessines += 1;
  });
  return {dessines: dessines, introuvables: introuvables,
          mal_placees: mal_placees, serrees: serrees};
}
"""


def age_des_donnees_en_minutes() -> float | None:
    """Depuis combien de temps le jeu de données a-t-il été chargé ?

    Une capture du kit — « la plage par défaut ne montre rien » — n'est vraie
    que si le jeu s'est terminé il y a plus de quinze minutes : le générateur
    ancre la fin de la fenêtre sur l'instant du chargement. Juste après
    « make data », les quinze dernières minutes CONTIENNENT des documents, et
    la capture montrerait le contraire de ce qu'elle annonce. Mieux vaut le
    dire que de laisser un délai d'attente expirer sans expliquer pourquoi.
    """
    chemin = conf.RACINE / "data" / "manifest.json"
    if not chemin.exists():
        return None
    engendre = json.loads(chemin.read_text(encoding="utf-8")).get("engendre_le")
    if not engendre:
        return None
    instant = datetime.datetime.fromisoformat(engendre)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=datetime.UTC)
    maintenant = datetime.datetime.now(datetime.UTC)
    return (maintenant - instant).total_seconds() / 60


def main() -> int:
    plan = yaml.safe_load((DOSSIER / "plan.yaml").read_text(encoding="utf-8"))

    age = age_des_donnees_en_minutes()
    exige = max(
        (c.get("age_minimal_donnees_min", 0) for c in plan), default=0
    )
    if exige and age is not None and age < exige:
        raise SystemExit(
            f"Données chargées il y a {age:.0f} min ; certaines captures en "
            f"exigent {exige}. La plage par défaut de Kibana n'est vide qu'une "
            f"fois ce délai passé — sans quoi la capture montrerait l'inverse "
            f"de sa légende.\n"
            f"Attendez {exige - age:.0f} min, puis relancez « make captures »."
        )
    SORTIE.mkdir(parents=True, exist_ok=True)
    produites = []

    with K.navigateur() as contexte:
        page = contexte.new_page()
        K.connexion(page)
        for capture in plan:
            K.aller_a(page, capture["chemin"], espace=capture.get("espace"))
            # Certains écrans n'existent qu'après un geste : le sélecteur de
            # type de graphique de Lens, par exemple, est un menu qu'il faut
            # ouvrir. Les gestes sont déclarés dans le plan, donc rejouables.
            gestes_ok = True
            for geste in capture.get("gestes") or []:
                cible = (f'[data-test-subj="{geste["clic"]}"]' if "clic" in geste
                         else f'button:has-text("{geste["clic_texte"]}")')
                try:
                    page.wait_for_selector(cible, timeout=45_000)
                    # Un bandeau d'information de Kibana intercepte parfois le
                    # clic : constaté sur Lens, plage de temps vide.
                    for toast in page.query_selector_all(
                            '[data-test-subj="toastCloseButton"]'):
                        try:
                            toast.click()
                        except Exception:
                            pass
                    page.click(cible, force=True)
                    page.wait_for_timeout(geste.get("attente_ms", 2_000))
                except Exception as erreur:
                    print(f"  [ÉCHEC] {capture['id']} : geste sur « {cible} » "
                          f"impossible ({type(erreur).__name__})")
                    gestes_ok = False
                    break
            if not gestes_ok:
                # On ne produit PAS une image qui ne montre pas ce qu'elle
                # annonce : « make captures » la déclarera manquante et sortira
                # en erreur, plutôt que de livrer un écran trompeur.
                continue
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
            annotation = page.evaluate(ANNOTATION, capture.get("reperes") or [])

            attendus = len(capture.get("reperes") or [])
            if annotation["dessines"] != attendus:
                print(f"  [ATTENTION] {capture['id']} : {annotation['dessines']} "
                      f"repère(s) dessiné(s) sur {attendus} — un sélecteur a "
                      f"changé ? ({', '.join(annotation['introuvables'])})")
            for serree in annotation.get("serrees") or []:
                print(f"  [ATTENTION] {capture['id']} : la pastille "
                      f"{serree['numero']} « {serree['cible']} » est posée sur "
                      f"une zone chargée — aucune place libre autour de sa cible")
            if annotation["mal_placees"]:
                # Une pastille rognée par le bord, ou posée sur ce qu'elle
                # désigne, rompt la correspondance légende ↔ image : c'est tout
                # l'intérêt d'une capture annotée. On ne livre pas la figure.
                for mauvaise in annotation["mal_placees"]:
                    if mauvaise.get("sans_place"):
                        raison = ("n'a aucune place libre autour de sa cible : "
                                  "les quatre positions candidates recouvrent "
                                  "du contenu ou sortent du cadre")
                    elif mauvaise["sort"]:
                        raison = "sort du cadre de la capture"
                    else:
                        raison = "recouvre l'élément qu'elle désigne"
                    print(f"  [ÉCHEC] {capture['id']} : la pastille "
                          f"{mauvaise['numero']} « {mauvaise['cible']} » "
                          f"{raison}")
                page.evaluate(
                    "() => document.getElementById('kit-reperes')?.remove()"
                )
                continue

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
