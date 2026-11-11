import argparse
import json
import sys
from collections import namedtuple
from datetime import date, datetime, timedelta
from functools import reduce
from pathlib import Path

# Tipos imutáveis
Disc = namedtuple("Disc", "nome dificuldade horas inicio prova")
Config = namedtuple("Config", "inicio lim_semana lim_sabado disciplinas")
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
etapas = lambda ini: lambda b: (
    Disc(f"{b['nome']} (GQ1)", int(b["dificuldade"]), float(b["horas"]) / 2,
         ini, data(b["gq1"])),
    Disc(f"{b['nome']} (GQ2)", int(b["dificuldade"]), float(b["horas"]) / 2,
         data(b["gq1"]) + timedelta(days=1), data(b["gq2"])),
)

parse_config = lambda bruto: (
    lambda ini: Config(
        ini,
        float(bruto["limite_semana"]),
        float(bruto["limite_sabado"]),
        tuple(t for b in bruto["disciplinas"] for t in etapas(ini)(b)),
    )
)(data(bruto["inicio"]))

erros_config = lambda cfg: (
    tuple(
        f"{d.nome}: dificuldade deve estar entre 1 e 5"
        for d in cfg.disciplinas
        if not 1 <= d.dificuldade <= 5
    )
    + tuple(
        f"{d.nome}: horas devem ser maiores que zero"
        for d in cfg.disciplinas
        if d.horas <= 0
    )
    + tuple(
        f"{d.nome}: a prova deve ser depois do início do estudo"
        for d in cfg.disciplinas
        if d.prova <= d.inicio
    )
    + (
        ("limites diários devem ser maiores que zero",)
        if min(cfg.lim_semana, cfg.lim_sabado) <= 0
        else ()
    )
)

validar = lambda cfg: (
    cfg
    if not erros_config(cfg)
    else sys.exit("Entrada inválida:\n- " + "\n- ".join(erros_config(cfg)))
)

EXEMPLO = {
    "inicio": "2027-02-22",
    "limite_semana": 4,
    "limite_sabado": 2,
    "disciplinas": [
        {"nome": "Ciência de Dados", "dificuldade": 4, "horas": 45,
         "gq1": "2027-04-10", "gq2": "2027-06-12"},
        {"nome": "Paradigmas", "dificuldade": 2, "horas": 30,
         "gq1": "2027-04-12", "gq2": "2027-06-14"},
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

# Saída: relatório (texto puro) e CSV
total_disc = lambda alocs, nome: round(
    sum(a.horas for a in alocs if a.nome == nome), 6
)

dias_livres = lambda plano: (
    lambda usados: tuple(d for d in plano.janela if d not in usados)
)({a.dia for a in plano.alocs})

linha_plano = lambda a: f"{fmt_d(a.dia)}  {a.nome:<24}{fmt_h(a.horas):>5} h"

linha_resumo = lambda alocs: lambda d: (
    f"- {d.nome}: {fmt_h(total_disc(alocs, d.nome))} h (prova em {fmt_d(d.prova)})"
)

bloco_aviso = lambda plano: (
    (
        "",
        "ATENÇÃO: horas sem alocação no tempo disponível:",
    )
    + tuple(f"- {n}: {fmt_h(h)} h" for n, h in plano.pendentes.items())
    if plano.pendentes
    else ()
)

relatorio = lambda cfg, plano: "\n".join(
    ("CRONOGRAMA DE ESTUDOS", "", "Dia    Disciplina              Horas", "-" * 38)
    + tuple(map(linha_plano, plano.alocs))
    + ("", "RESUMO")
    + tuple(map(linha_resumo(plano.alocs), ordenar(cfg.disciplinas)))
    + (
        "",
        f"Total: {fmt_h(sum(a.horas for a in plano.alocs))} h em "
        f"{len({a.dia for a in plano.alocs})} dia(s), "
        f"limite de {fmt_h(cfg.limite)} h/dia.",
        "Dias livres para revisão: "
        + (", ".join(map(fmt_d, dias_livres(plano))) or "nenhum"),
    )
    + bloco_aviso(plano)
)

csv_texto = lambda alocs: (
    "\n".join(
        ("dia,disciplina,horas",)
        + tuple(
            f"{a.dia:%d/%m/%Y},{aspas(a.nome)},{fmt_h(a.horas)}" for a in alocs
        )
    )
    + "\n"
)

pipeline = compor(
    parse_config,
    validar,
    lambda cfg: (cfg, planejar(cfg)),
    lambda t: (t[1], relatorio(t[0], t[1])),
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gerador de cronograma de estudos")
    ap.add_argument("entrada", nargs="?", help="arquivo JSON (padrão: exemplo da proposta)")
    ap.add_argument("--csv", help="salva o plano em um arquivo CSV")
    args = ap.parse_args()

    bruto = (
        json.loads(Path(args.entrada).read_text(encoding="utf-8"))
        if args.entrada
        else EXEMPLO
    )
    plano, texto = pipeline(bruto)
    print(texto)
    args.csv and Path(args.csv).write_text(csv_texto(plano.alocs), encoding="utf-8")