import argparse
import json
import sys
from collections import namedtuple
from datetime import date, datetime, timedelta
from functools import reduce
from pathlib import Path

# Tipos imutáveis
Disc = namedtuple("Disc", "nome peso dificuldade prova")
Config = namedtuple("Config", "inicio limite fator disciplinas")
Alocacao = namedtuple("Alocacao", "dia nome horas")
Plano = namedtuple("Plano", "janela alocs pendentes")

# Utilitários puros
compor = lambda *fs: lambda x: reduce(lambda acc, f: f(acc), fs, x)

data = lambda s: (
    datetime.strptime(s, "%d/%m/%Y").date() if "/" in s else date.fromisoformat(s)
)
fmt_h = lambda h: f"{h:g}"
fmt_d = lambda d: f"{d:%d/%m}"
aspas = lambda s: '"' + s.replace('"', '""') + '"'

# Entrada

parse_config = lambda bruto: Config(
    data(bruto["inicio"]),
    float(bruto["limite_diario"]),
    float(bruto.get("fator", 1)),
    tuple(
        Disc(d["nome"], int(d["peso"]), int(d["dificuldade"]), data(d["prova"]))
        for d in bruto["disciplinas"]
    ),
)

erros_config = lambda cfg: (
    tuple(
        f"{d.nome}: peso e dificuldade devem estar entre 1 e 5"
        for d in cfg.disciplinas
        if not (1 <= d.peso <= 5 and 1 <= d.dificuldade <= 5)
    )
    + (("limite diário deve ser maior que zero",) if cfg.limite <= 0 else ())
)

validar = lambda cfg: (
    cfg
    if not erros_config(cfg)
    else sys.exit("Entrada inválida:\n- " + "\n- ".join(erros_config(cfg)))
)

EXEMPLO = {
    "inicio": "2026-11-02",
    "limite_diario": 4,
    "disciplinas": [
        {"nome": "Ciência de Dados", "peso": 3, "dificuldade": 4, "prova": "2026-11-06"},
        {"nome": "Computação Gráfica", "peso": 2, "dificuldade": 3, "prova": "2026-11-09"},
        {"nome": "Paradigmas", "peso": 2, "dificuldade": 2, "prova": "2026-11-10"},
    ],
}