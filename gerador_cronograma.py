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

horas_necessarias = lambda fator: lambda d: d.peso * d.dificuldade * fator

# prova mais próxima primeiro (desempate pelo nome)
ordenar = lambda ds: sorted(ds, key=lambda d: (d.prova, d.nome))

dias = lambda ini, fim: tuple(
    ini + timedelta(days=i) for i in range((fim - ini).days + 1)
)

# estado = (restante: {nome: horas}, livre_no_dia, alocacoes_do_dia)
passo_disc = lambda dia: lambda e, d: (
    lambda h: (
        {**e[0], d.nome: round(e[0][d.nome] - h, 6)},
        round(e[1] - h, 6),
        e[2] + ((Alocacao(dia, d.nome, h),) if h > 0 else ()),
    )
)(min(e[0][d.nome], e[1]) if dia < d.prova else 0)  # só estuda até a véspera

# estado = (restante, alocacoes_acumuladas)
aloca_dia = lambda ordenadas, limite: lambda estado, dia: (
    lambda r: (r[0], estado[1] + r[2])
)(reduce(passo_disc(dia), ordenadas, (estado[0], limite, ())))

planejar = lambda cfg: (
    lambda ordenadas, janela, inicial: (
        lambda final: Plano(
            janela,
            final[1],
            {n: h for n, h in final[0].items() if h > 0},
        )
    )(reduce(aloca_dia(ordenadas, cfg.limite), janela, (inicial, ())))
)(
    ordenar(cfg.disciplinas),
    dias(
        cfg.inicio,
        max((d.prova for d in cfg.disciplinas), default=cfg.inicio)
        - timedelta(days=1),
    ),
    {d.nome: horas_necessarias(cfg.fator)(d) for d in cfg.disciplinas},
)