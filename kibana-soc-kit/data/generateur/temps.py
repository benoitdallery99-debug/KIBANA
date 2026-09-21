"""Modèle temporel des données — SPEC §5.1.

Les données sont ancrées sur l'instant du chargement : la fenêtre se termine à
T0. Les réponses attendues sont donc des VALEURS (adresse, compte, nombre),
jamais des dates absolues, qui seraient fausses dès le lendemain.

Le rythme métier est défini dans le fuseau de l'organisation
(donnees.fuseau_metier) ; les horodatages sont stockés en UTC, comme le fait
Elasticsearch.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

# Poids horaires d'une journée ouvrée, dans le fuseau métier.
# Le creux nocturne n'est pas nul : une organisation conserve des traitements
# automatiques la nuit, et c'est ce fond qui rend le scénario S4 (exfiltration
# nocturne) détectable sans être évident.
POIDS_HEURES_OUVREES = [
    2, 1, 1, 1, 1, 2, 4, 10,      # 00h → 07h
    28, 42, 48, 45, 30, 38, 46, 44,  # 08h → 15h
    40, 34, 22, 12, 8, 6, 4, 3,   # 16h → 23h
]
# Le week-end garde une activité résiduelle (astreintes, traitements planifiés).
FACTEUR_SAMEDI = 0.16
FACTEUR_DIMANCHE = 0.10


def maintenant() -> datetime:
    """T0 : fin de la fenêtre de données, à la seconde."""
    return datetime.now(UTC).replace(microsecond=0)


def debut_fenetre(t0: datetime, jours: int) -> datetime:
    return t0 - timedelta(days=jours)


def poids_de_l_heure(instant_utc: datetime, fuseau: str) -> float:
    """Poids d'activité d'une heure donnée, selon le fuseau métier."""
    local = instant_utc.astimezone(ZoneInfo(fuseau))
    poids = float(POIDS_HEURES_OUVREES[local.hour])
    jour = local.weekday()  # 0 = lundi
    if jour == 5:
        poids *= FACTEUR_SAMEDI
    elif jour == 6:
        poids *= FACTEUR_DIMANCHE
    return poids


def horodatages(
    rng: random.Random,
    combien: int,
    t0: datetime,
    jours: int,
    fuseau: str,
) -> list[datetime]:
    """Répartit « combien » horodatages sur la fenêtre, au rythme métier.

    La répartition est faite heure par heure, proportionnellement au poids de
    chaque heure, puis uniformément à l'intérieur de l'heure.
    """
    debut = debut_fenetre(t0, jours)
    heures: list[datetime] = []
    curseur = debut.replace(minute=0, second=0, microsecond=0)
    while curseur < t0:
        heures.append(curseur)
        curseur += timedelta(hours=1)

    poids = [poids_de_l_heure(h, fuseau) for h in heures]
    total = sum(poids)
    if total <= 0:
        return []

    resultat: list[datetime] = []
    for heure, p in zip(heures, poids, strict=True):
        part = combien * p / total
        # Partie entière, puis tirage pour la fraction : le total reste proche
        # de « combien » sans introduire de biais systématique.
        nombre = int(part) + (1 if rng.random() < (part - int(part)) else 0)
        for _ in range(nombre):
            instant = heure + timedelta(seconds=rng.randrange(3600))
            if debut <= instant < t0:
                resultat.append(instant)
    resultat.sort()
    return resultat


def nuit(instant_utc: datetime, fuseau: str) -> bool:
    """Vrai entre 23 h et 5 h dans le fuseau métier (créneau du scénario S4)."""
    heure = instant_utc.astimezone(ZoneInfo(fuseau)).hour
    return heure >= 23 or heure < 5


def iso(instant: datetime) -> str:
    """Horodatage ISO 8601 en UTC, format accepté tel quel par Elasticsearch."""
    return instant.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
