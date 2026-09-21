"""Matrice objectifs × exercices × questions — SPEC §2 et §9.

Chaque objectif pédagogique doit être évalué par au moins UN exercice ET UNE
question du quiz. Ce script le prouve ou le réfute ; il sort en 1 si la
couverture est incomplète, pour que « make verif » s'en aperçoive.

Il écrit aussi formateur/matrice.md, repris dans le guide formateur.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outils import conf

PARCOURS = conf.RACINE / "parcours"
QUIZ = conf.RACINE / "formateur" / "quiz.yaml"
SORTIE = conf.RACINE / "formateur" / "matrice.md"


def charger_modules() -> list[dict]:
    modules = []
    for chemin in sorted(PARCOURS.glob("M*.md")):
        texte = chemin.read_text(encoding="utf-8")
        _, brut, _ = texte.split("---", 2)
        modules.append(yaml.safe_load(brut))
    return modules


def main() -> int:
    modules = charger_modules()
    if not modules:
        print("Aucun module : matrice impossible.", file=sys.stderr)
        return 1

    objectifs: dict[str, dict] = {}
    for module in modules:
        for objectif in module.get("objectifs") or []:
            objectifs[objectif["id"]] = {
                "module": module["id"],
                "enonce": objectif["enonce"],
                "exercices": [],
                "questions": [],
            }

    for module in modules:
        for exercice in module.get("exercices") or []:
            for identifiant in exercice.get("objectifs") or []:
                if identifiant in objectifs:
                    objectifs[identifiant]["exercices"].append(exercice["id"])

    quiz = []
    if QUIZ.exists():
        quiz = yaml.safe_load(QUIZ.read_text(encoding="utf-8")) or []
        for question in quiz:
            for identifiant in question.get("objectifs") or []:
                if identifiant in objectifs:
                    objectifs[identifiant]["questions"].append(question["id"])

    sans_exercice = [i for i, o in objectifs.items() if not o["exercices"]]
    sans_question = [i for i, o in objectifs.items() if not o["questions"]]

    lignes = [
        "# Matrice objectifs × exercices × questions",
        "",
        "Engendrée par `formateur/matrice.py`. Chaque objectif doit être couvert par",
        "au moins un exercice **et** une question du quiz (SPEC §2).",
        "",
        f"- Objectifs : **{len(objectifs)}**",
        f"- Exercices : **{sum(len(m.get('exercices') or []) for m in modules)}**",
        f"- Questions du quiz : **{len(quiz)}**",
        "",
        "| Objectif | Module | Exercices | Questions |",
        "|---|---|---|---|",
    ]
    for identifiant, objectif in objectifs.items():
        lignes.append(
            f"| `{identifiant}` | {objectif['module']} | "
            f"{', '.join(objectif['exercices']) or '**aucun**'} | "
            f"{', '.join(objectif['questions']) or '**aucune**'} |"
        )

    lignes += ["", "## Énoncés", ""]
    for identifiant, objectif in objectifs.items():
        lignes.append(f"- **{identifiant}** — {objectif['enonce']}")

    if sans_exercice or sans_question:
        lignes += ["", "## Couverture incomplète", ""]
        if sans_exercice:
            lignes.append(f"- Sans exercice : {', '.join(sans_exercice)}")
        if sans_question:
            lignes.append(f"- Sans question de quiz : {', '.join(sans_question)}")

    SORTIE.write_text("\n".join(lignes) + "\n", encoding="utf-8")

    couverts = len(objectifs) - len(set(sans_exercice) | set(sans_question))
    taux = 100 * couverts / len(objectifs) if objectifs else 0
    print(f"Objectifs : {len(objectifs)} · exercices : "
          f"{sum(len(m.get('exercices') or []) for m in modules)} · questions : {len(quiz)}")
    print(f"Couverture complète (exercice ET question) : {couverts}/{len(objectifs)} "
          f"soit {taux:.0f} %")
    print(f"Matrice écrite : {SORTIE.relative_to(conf.RACINE)}")

    if sans_exercice:
        print(f"ÉCHEC — objectifs sans exercice : {sans_exercice}", file=sys.stderr)
    if sans_question:
        print(f"ÉCHEC — objectifs sans question : {sans_question}", file=sys.stderr)
    return 1 if (sans_exercice or sans_question) else 0


if __name__ == "__main__":
    raise SystemExit(main())
