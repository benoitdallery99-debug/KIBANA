"""Matrice objectifs × exercices × questions — SPEC §2 et §9.

Chaque objectif pédagogique doit être évalué par au moins UN exercice ET UNE
question du quiz. Ce script le prouve ou le réfute ; il sort en 1 si la
couverture est incomplète, pour que « make verif » s'en aperçoive.

Il contrôle aussi la forme des propositions du quiz : si la bonne réponse est
la proposition la plus longue dans plus d'un quart des questions, cocher la
plus longue suffit à passer l'évaluation, et le script sort en 1.

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

# Part maximale de questions où la bonne réponse est la proposition la plus
# longue. Au-delà, la longueur devient une stratégie : on coche la plus longue
# sans lire l'énoncé. Le quiz avait atteint 14 questions sur 17, soit 82 % de
# bonnes réponses sans aucune connaissance — autant que le meilleur stagiaire.
# Quatre propositions donnent 25 % au hasard pur : tant que la clé n'est la plus
# longue que dans un quart des questions, la longueur ne rapporte pas plus que
# le hasard.
PART_MAXIMALE_CLE_LA_PLUS_LONGUE = 0.25


def cles_les_plus_longues(quiz: list[dict]) -> list[str]:
    """Questions où la bonne réponse est, à elle seule, la plus longue.

    L'égalité ne compte pas : deux propositions de même longueur ne désignent
    rien. Seul le maximum STRICT est un indice exploitable par le stagiaire.
    """
    reperees = []
    for question in quiz:
        longueurs = [len(str(p).strip()) for p in question.get("propositions") or []]
        rang = question.get("reponse")
        if not longueurs or not isinstance(rang, int) or not 0 <= rang < len(longueurs):
            continue
        if longueurs[rang] == max(longueurs) and longueurs.count(max(longueurs)) == 1:
            reperees.append(question["id"])
    return reperees


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
    plus_longues = cles_les_plus_longues(quiz)
    part_plus_longues = len(plus_longues) / len(quiz) if quiz else 0.0

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

    lignes += [
        "",
        "## Longueur des propositions du quiz",
        "",
        f"La bonne réponse est la proposition la plus longue dans "
        f"**{len(plus_longues)}** question(s) sur **{len(quiz)}** "
        f"(soit {100 * part_plus_longues:.0f} %), pour un plafond de "
        f"{100 * PART_MAXIMALE_CLE_LA_PLUS_LONGUE:.0f} % : "
        + (", ".join(plus_longues) if plus_longues else "aucune")
        + ".",
    ]

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
    print(f"Bonne réponse = proposition la plus longue : {len(plus_longues)}/{len(quiz)} "
          f"soit {100 * part_plus_longues:.0f} % "
          f"(plafond {100 * PART_MAXIMALE_CLE_LA_PLUS_LONGUE:.0f} %)")
    print(f"Matrice écrite : {SORTIE.relative_to(conf.RACINE)}")

    if sans_exercice:
        print(f"ÉCHEC — objectifs sans exercice : {sans_exercice}", file=sys.stderr)
    if sans_question:
        print(f"ÉCHEC — objectifs sans question : {sans_question}", file=sys.stderr)
    trop_longues = part_plus_longues > PART_MAXIMALE_CLE_LA_PLUS_LONGUE
    if trop_longues:
        print(
            f"ÉCHEC — la bonne réponse est la proposition la plus longue dans "
            f"{len(plus_longues)}/{len(quiz)} questions "
            f"(soit {100 * part_plus_longues:.0f} %), au-delà des "
            f"{100 * PART_MAXIMALE_CLE_LA_PLUS_LONGUE:.0f} % tolérés : "
            f"{plus_longues}. Cocher la plus longue rapporterait autant qu'avoir "
            f"suivi la journée : étoffer les distracteurs des questions citées.",
            file=sys.stderr,
        )
    return 1 if (sans_exercice or sans_question or trop_longues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
