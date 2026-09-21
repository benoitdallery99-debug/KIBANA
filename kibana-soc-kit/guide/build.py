"""Construit dist/guide.html — un seul fichier, aucune ressource externe.

Règle cardinale : le guide n'embarque JAMAIS une réponse attendue, seulement
les empreintes SHA-256 des réponses normalisées. La construction recopie donc
champ par champ ce qui a le droit de sortir, au lieu de verser le manifeste
dans le gabarit et d'espérer.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import markdown as md
import yaml
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf
from outils.fuites import chercher as chercher_fuites
from outils.typographie import corriger_html

GUIDE = conf.RACINE / "guide"
DIST = conf.RACINE / "dist"

GUIDAGES = {
    "demonstration": "démonstration",
    "guide": "guidé",
    "semi-guide": "semi-guidé",
    "autonome": "autonome",
}


def frontmatter(texte: str) -> tuple[dict, str]:
    if not texte.startswith("---"):
        raise SystemExit("frontmatter YAML absent")
    _, brut, corps = texte.split("---", 2)
    return yaml.safe_load(brut), corps


def css_avec_polices() -> str:
    """Inline les polices en base64, telles que distribuées (CLAUDE.md).

    Aucun sous-ensemble, aucune conversion : ce sont des polices OFL à noms
    réservés, et le fichier officiel est embarqué tel quel.
    """
    css = (GUIDE / "styles" / "guide.css").read_text(encoding="utf-8")
    polices = {
        "__POLICE_TEXTE__": "AtkinsonHyperlegibleNext[wght].ttf",
        "__POLICE_ITALIQUE__": "AtkinsonHyperlegibleNext-Italic[wght].ttf",
        "__POLICE_MONO__": "AtkinsonHyperlegibleMono[wght].ttf",
    }
    for marque, nom in polices.items():
        chemin = GUIDE / "polices" / nom
        if not chemin.exists():
            raise SystemExit(f"police absente : {chemin}")
        encode = base64.b64encode(chemin.read_bytes()).decode("ascii")
        css = css.replace(marque, f"data:font/ttf;base64,{encode}")
    return css


def captures_par_module() -> dict[str, list[dict]]:
    """Charge les captures produites et les inline en WebP base64.

    Une capture manquante n'interrompt pas la construction : elle est signalée.
    Le guide doit rester constructible avant « make captures », sinon on ne
    peut plus travailler le texte sans lab démarré.
    """
    plan_chemin = conf.RACINE / "captures" / "plan.yaml"
    if not plan_chemin.exists():
        return {}
    plan = yaml.safe_load(plan_chemin.read_text(encoding="utf-8")) or []
    par_module: dict[str, list[dict]] = {}
    manquantes = []
    for capture in plan:
        fichier = conf.RACINE / "captures" / "images" / f"{capture['id']}.webp"
        if not fichier.exists():
            manquantes.append(capture["id"])
            continue
        encode = base64.b64encode(fichier.read_bytes()).decode("ascii")
        par_module.setdefault(capture["module"], []).append({
            "id": capture["id"],
            "titre": capture["titre"],
            "legende": capture.get("legende", ""),
            "alt": capture["alt"],
            "reperes": capture.get("reperes") or [],
            "source": f"data:image/webp;base64,{encode}",
        })
    if manquantes:
        print(f"  (captures absentes, ignorées : {', '.join(manquantes)} — "
              f"lancez « make captures »)")
    return par_module


def markdown_vers_html(texte: str) -> str:
    html = md.markdown(
        texte,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "def_list"],
        output_format="html",
    )
    # Un bloc de code long défile horizontalement dans son cadre. Une zone qui
    # défile doit être atteignable au clavier, sans quoi son contenu est
    # inaccessible à qui n'emploie pas la souris — axe-core le signale en
    # « serious » (scrollable-region-focusable). « tabindex=0 » la rend
    # focalisable ; le lecteur d'écran annonce alors un groupe qu'on peut
    # parcourir aux flèches.
    return html.replace("<pre>", '<pre tabindex="0">')


def exercice_public(exercice: dict, reponses: dict, pieges: dict, module_id: str) -> dict:
    """Ne laisse sortir que ce qui a le droit d'être publié.

    En particulier : la réponse attendue n'est PAS recopiée ; seules ses
    empreintes le sont, ainsi que sa règle de normalisation, pour que le guide
    puisse dire « juste » ou « faux » sans jamais connaître la valeur.
    """
    sortie = {
        "id": exercice["id"],
        "ancre": f"ex-{exercice['id'].lower()}",
        "titre": exercice["titre"],
        "guidage": exercice["guidage"],
        "guidage_libelle": GUIDAGES.get(exercice["guidage"], exercice["guidage"]),
        "duree_minutes": exercice.get("duree_minutes", 0),
        "contexte": exercice.get("contexte", ""),
        "consignes": exercice.get("consignes") or [],
        "indices": exercice.get("indices") or [],
        "format_de_reponse": exercice.get("format_de_reponse", "une valeur"),
        "solution": exercice.get("solution", ""),
        "erreurs_typiques": exercice.get("erreurs_typiques") or [],
        "doc": exercice.get("doc", ""),
        "requetes": [],
        "piege": None,
        "reponse": None,
    }

    # Un exercice « autonome » ne publie PAS ses requêtes. Elles existent pour
    # que la suite de vérification rejoue l'exercice sur le lab ; les afficher
    # au stagiaire livrerait la démarche que l'exercice lui demande justement
    # de trouver seul — c'est tout ce qui distingue « autonome » de « guidé ».
    autonome = exercice.get("guidage") == "autonome"

    for i, requete in enumerate([] if autonome else exercice.get("requetes_kql") or []):
        if not requete.get("kql"):
            continue
        sortie["requetes"].append({
            "id": f"q-{exercice['id'].lower()}-{i}",
            "langage": "KQL",
            "texte": requete["kql"],
        })
    for i, requete in enumerate([] if autonome else exercice.get("requetes_esql") or []):
        sortie["requetes"].append({
            "id": f"e-{exercice['id'].lower()}-{i}",
            "langage": "ES|QL",
            "texte": requete["esql"] if isinstance(requete, dict) else str(requete),
        })

    identifiant_piege = exercice.get("piege")
    if identifiant_piege and identifiant_piege in pieges:
        p = pieges[identifiant_piege]
        sortie["piege"] = {"titre": p["titre"], "lecon": p["lecon"]}

    renvoi = exercice.get("reponse")
    if renvoi:
        cle = f"{renvoi['scenario']}.{renvoi['cle']}"
        if cle not in reponses:
            raise SystemExit(f"{exercice['id']} : renvoi « {cle} » absent du manifeste")
        reponse = reponses[cle]
        sortie["reponse"] = {
            # Les empreintes, la règle de normalisation, rien d'autre.
            "empreintes": reponse["empreintes"],
            "normalisation": reponse.get("normalisation", "espaces retirés"),
            # Seuls les scénarios cachés alimentent la rangée d'enquête ; les
            # repères n'y figurent pas, ils ne sont pas une énigme.
            "scenario_public": renvoi["scenario"] if renvoi["scenario"].startswith("S") else "",
        }
    return sortie


def contexte_du_manifeste(manifeste: dict) -> dict:
    return manifeste["contexte"]


def charger_modules() -> tuple[dict, list[dict], list[dict]]:
    """Charge manifeste, modules et glossaire. Source unique du HTML et des PDF."""
    manifeste = json.loads((conf.RACINE / "data" / "manifest.json").read_text(encoding="utf-8"))
    blocs = [manifeste["reperes"], *manifeste["scenarios"]]
    reponses = {f"{b['id']}.{r['cle']}": r for b in blocs for r in b["reponses"]}

    chemin_pieges = conf.RACINE / "docs" / "pieges-lab.json"
    pieges = {}
    if chemin_pieges.exists():
        pieges = {
            p["id"]: p
            for p in json.loads(chemin_pieges.read_text(encoding="utf-8"))["pieges"]
        }

    captures = captures_par_module()

    modules = []
    for chemin in sorted((conf.RACINE / "parcours").glob("M*.md")):
        entete, corps = frontmatter(chemin.read_text(encoding="utf-8"))
        modules.append({
            "captures": captures.get(entete["id"], []),
            "id": entete["id"],
            "ancre": f"module-{entete['id'].lower()}",
            "titre": entete["titre"],
            "resume": entete.get("resume", ""),
            "duree_minutes": entete.get("duree_minutes", 0),
            "objectifs": entete.get("objectifs") or [],
            "rappel_actif": entete.get("rappel_actif") or [],
            "corps_html": markdown_vers_html(corps),
            "exercices": [
                exercice_public(e, reponses, pieges, entete["id"])
                for e in (entete.get("exercices") or [])
            ],
        })
    if not modules:
        raise SystemExit("aucun module dans parcours/ : rien à construire")

    glossaire = yaml.safe_load((GUIDE / "glossaire.yaml").read_text(encoding="utf-8"))
    return manifeste, modules, glossaire


def charger_quiz() -> list[dict]:
    """Le quiz, avec ses réponses et ses explications.

    Contrairement aux exercices, le quiz PEUT embarquer ses réponses : SPEC §9
    prévoit une version intégrée au guide qui explique chaque réponse. C'est un
    contrôle de connaissances, pas une enquête à mener.
    """
    chemin = conf.RACINE / "formateur" / "quiz.yaml"
    if not chemin.exists():
        return []
    return yaml.safe_load(chemin.read_text(encoding="utf-8")) or []


def main() -> int:
    manifeste, modules, glossaire = charger_modules()
    quiz = charger_quiz()

    env = Environment(
        loader=FileSystemLoader(str(GUIDE / "gabarits")),
        # PIÈGE : select_autoescape(["html"]) compare la DERNIÈRE extension du
        # fichier. Nos gabarits s'appellent « guide.html.j2 » : leur extension
        # est « .j2 », l'échappement restait donc désactivé partout, et tout
        # « & », « < » ou guillemet venant du parcours partait tel quel dans la
        # page. On l'active sans condition — tous les gabarits sont du HTML — et
        # le seul fragment volontairement injecté, « corps_html », est marqué
        # « | safe » dans les gabarits.
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    gabarit = env.get_template("guide.html.j2")

    html = gabarit.render(
        titre="Kibana pour analystes SOC",
        sous_titre=(
            "Parcours pratique : chercher, visualiser, et rendre le résultat "
            "durable sous forme de tableau de bord."
        ),
        version=conf.version(),
        licence=str(conf.valeur("stack.licence")).capitalize(),
        locale=str(conf.valeur("kibana.locale")),
        duree_totale=sum(m["duree_minutes"] for m in modules),
        contexte=manifeste["contexte"],
        modules=modules,
        scenarios=[s["id"] for s in manifeste["scenarios"]],
        glossaire=glossaire,
        quiz=quiz,
        avertissement_donnees=manifeste["avertissement"],
        css=css_avec_polices(),
        js=(GUIDE / "js" / "guide.js").read_text(encoding="utf-8"),
        theme_force=None,
    )

    # Typographie française appliquée au rendu, hors code (CLAUDE.md).
    html = corriger_html(html)

    # Garde-fou : aucune réponse attendue ne doit avoir fui dans le rendu,
    # hors ce que la fiche de contexte publie légitimement (voir outils/fuites).
    fuites = chercher_fuites(html, manifeste)
    if fuites:
        raise SystemExit(
            "CONSTRUCTION REFUSÉE — des réponses attendues figurent dans le guide :\n  "
            + "\n  ".join(fuites)
        )

    DIST.mkdir(parents=True, exist_ok=True)
    cible = DIST / "guide.html"
    cible.write_text(html, encoding="utf-8")

    taille = cible.stat().st_size
    externes = re.findall(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)', html)
    print(f"  {cible.relative_to(conf.RACINE)} — {taille / 1024 / 1024:.2f} Mo, "
          f"{len(modules)} modules, "
          f"{sum(len(m['exercices']) for m in modules)} exercices, "
          f"{len(quiz)} questions de quiz")
    print(f"  liens externes dans le document : {len(externes)} "
          f"(uniquement des liens de documentation, jamais chargés)")
    if taille > 20 * 1024 * 1024:
        raise SystemExit(f"guide de {taille / 1024 / 1024:.1f} Mo : la limite est 20 Mo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
