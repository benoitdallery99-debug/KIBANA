"""Gabarits d'index (index templates) des data streams du kit — SPEC §5.1.

Trois exigences y sont tenues :
1. Priorité supérieure à celle des gabarits intégrés d'Elastic (100 pour
   « logs-*-* »), sans quoi nos mappings ne s'appliqueraient pas.
2. Typage explicite : « ip » pour les adresses, « keyword » pour les
   identifiants, « date », « long ». Un champ mal typé rendrait faux tout le
   parcours — une recherche CIDR est impossible sur un keyword, une comparaison
   numérique impossible sur du texte.
3. « index.mode » fixé explicitement : voir MODE_INDEX ci-dessous.
"""

from __future__ import annotations

# Au-dessus des gabarits intégrés d'Elastic pour « logs-*-* » (priorité 100).
PRIORITE = 500

ECS_VERSION = "8.11.0"

# Le mode d'index est fixé à « standard » et non laissé au défaut.
# En 9.x, les gabarits intégrés peuvent placer les data streams « logs-*-* » en
# mode « logsdb », qui active le _source synthétique : le document réaffiché
# dans Discover est alors reconstruit, ses champs réordonnés et certaines
# valeurs normalisées. Pour un parcours de formation, le stagiaire doit voir
# dans Discover exactement ce qui a été indexé. Le choix est donc « standard »,
# et la différence est signalée au stagiaire dans le module M5.
MODE_INDEX = "standard"

# --- Champs communs à toutes les sources ------------------------------------
COMMUNS: dict = {
    "@timestamp": {"type": "date"},
    "ecs": {"properties": {"version": {"type": "keyword"}}},
    # « message » est volontairement du texte analysé : c'est le contraste avec
    # les champs keyword qui fait comprendre, en M1, pourquoi une recherche est
    # sensible à la casse sur les uns et pas sur l'autre.
    "message": {"type": "text"},
    "event": {
        "properties": {
            "kind": {"type": "keyword"},
            "category": {"type": "keyword"},
            "type": {"type": "keyword"},
            "action": {"type": "keyword"},
            "outcome": {"type": "keyword"},
            "code": {"type": "keyword"},
            "dataset": {"type": "keyword"},
            "module": {"type": "keyword"},
            "severity": {"type": "long"},
            "duration": {"type": "long"},
        }
    },
    "host": {
        "properties": {
            "name": {"type": "keyword"},
            "ip": {"type": "ip"},
            "os": {"properties": {"type": {"type": "keyword"}}},
        }
    },
    "source": {
        "properties": {
            "ip": {"type": "ip"},
            "port": {"type": "long"},
            "bytes": {"type": "long"},
        }
    },
    "destination": {
        "properties": {
            "ip": {"type": "ip"},
            "port": {"type": "long"},
            "bytes": {"type": "long"},
        }
    },
    "network": {
        "properties": {
            "transport": {"type": "keyword"},
            "protocol": {"type": "keyword"},
            "direction": {"type": "keyword"},
        }
    },
    "user": {
        "properties": {
            "name": {"type": "keyword"},
            "domain": {"type": "keyword"},
        }
    },
    "observer": {
        "properties": {
            "type": {"type": "keyword"},
            "name": {"type": "keyword"},
            "vendor": {"type": "keyword"},
        }
    },
    "organization": {"properties": {"name": {"type": "keyword"}}},
}

# --- Champs propres à certaines sources -------------------------------------
PARTICULIERS: dict[str, dict] = {
    "windows.security": {
        "winlog": {
            "properties": {
                "channel": {"type": "keyword"},
                "logon": {"properties": {"type": {"type": "keyword"}}},
            }
        },
        "process": {"properties": {"name": {"type": "keyword"}}},
    },
    "linux.auth": {
        "process": {
            "properties": {
                "name": {"type": "keyword"},
                "pid": {"type": "long"},
            }
        },
    },
    "ids.alert": {
        "rule": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "keyword"},
                "category": {"type": "keyword"},
            }
        },
        "threat": {
            "properties": {
                "tactic": {"properties": {"name": {"type": "keyword"}}},
            }
        },
    },
    "network.dns": {
        "dns": {
            "properties": {
                "question": {
                    "properties": {
                        "name": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "registered_domain": {"type": "keyword"},
                    }
                },
                "response_code": {"type": "keyword"},
                "resolved_ip": {"type": "ip"},
            }
        },
    },
    "proxy.web": {
        "url": {
            "properties": {
                "domain": {"type": "keyword"},
                "path": {"type": "keyword"},
                "full": {"type": "keyword"},
                "scheme": {"type": "keyword"},
            }
        },
        "http": {
            "properties": {
                "request": {"properties": {"method": {"type": "keyword"}}},
                "response": {"properties": {"status_code": {"type": "long"}}},
            }
        },
        "user_agent": {"properties": {"name": {"type": "keyword"}}},
    },
    "firewall.traffic": {
        "rule": {"properties": {"name": {"type": "keyword"}, "id": {"type": "keyword"}}},
    },
}

# Les six sources du kit (SPEC §5.2). Le dataset ne contient pas de tiret :
# c'est une contrainte de nommage des data streams.
DATASETS: dict[str, str] = {
    "windows.security": "Authentification Windows",
    "linux.auth": "Authentification SSH",
    "ids.alert": "Alertes IDS",
    "network.dns": "DNS",
    "proxy.web": "Proxy web",
    "firewall.traffic": "Pare-feu",
}


def nom_data_stream(dataset: str, namespace: str) -> str:
    return f"logs-{dataset}-{namespace}"


def gabarit(dataset: str, namespace: str) -> dict:
    """Construit le gabarit d'index d'un dataset, pour un namespace donné."""
    proprietes = {**COMMUNS}
    for cle, valeur in PARTICULIERS.get(dataset, {}).items():
        if cle in proprietes:
            # Fusion peu profonde des sous-propriétés (ex. « process » déjà commun).
            fusion = {**proprietes[cle].get("properties", {}), **valeur.get("properties", {})}
            proprietes[cle] = {"properties": fusion}
        else:
            proprietes[cle] = valeur

    return {
        "index_patterns": [nom_data_stream(dataset, namespace)],
        "data_stream": {},
        "priority": PRIORITE,
        "_meta": {
            "origine": "kit de formation Kibana pour analystes SOC",
            "source": DATASETS[dataset],
            "avertissement": "Données entièrement synthétiques (SPEC §5.1).",
        },
        "template": {
            "settings": {
                # Nœud unique : sans réplica, la santé du cluster est « green ».
                "index.number_of_replicas": 0,
                "index.number_of_shards": 1,
                "index.mode": MODE_INDEX,
                # Le champ « message » est le seul texte analysé : on garde
                # l'analyseur par défaut, c'est celui de la production.
                "index.refresh_interval": "5s",
            },
            "mappings": {
                # Aucun champ deviné : un champ absent du mapping est un défaut,
                # pas une commodité.
                "dynamic": "strict",
                "_meta": {"ecs_version": ECS_VERSION},
                "properties": proprietes,
            },
        },
    }


def tous_les_gabarits(namespace: str) -> dict[str, dict]:
    return {
        f"kit-soc-{dataset}-{namespace}": gabarit(dataset, namespace)
        for dataset in DATASETS
    }
