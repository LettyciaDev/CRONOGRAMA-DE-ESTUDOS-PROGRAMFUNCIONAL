import json
from datetime import date

import pandas as pd
import streamlit as st

from gerador_cronograma import (
    EXEMPLO,
    csv_texto,
    dias_livres,
    fase,
    ordenar,
    pipeline,
    progresso,
    total_disc,
)

st.set_page_config(page_title="Cronograma de Estudos", page_icon="📚", layout="wide")

DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
ICONES = {"teoria": "📘 teoria", "lista": "📝 lista", "revisão": "🔁 revisão"}


# ---------- dados iniciais (vêm do EXEMPLO do gerador) ----------
def tabela_inicial():
    return pd.DataFrame(
        [
            {
                "Disciplina": d["nome"],
                "Dificuldade": d["dificuldade"],
                "Horas no semestre": float(d["horas"]),
                "Prova GQ1": date.fromisoformat(d["gq1"]),
                "Prova GQ2": date.fromisoformat(d["gq2"]),
            }
            for d in EXEMPLO["disciplinas"]
        ]
    )


def monta_entrada(inicio, lim_semana, lim_sabado, tabela):
    return {
        "inicio": inicio.isoformat(),
        "limite_semana": lim_semana,
        "limite_sabado": lim_sabado,
        "disciplinas": [
            {
                "nome": r["Disciplina"],
                "dificuldade": int(r["Dificuldade"]),
                "horas": float(r["Horas no semestre"]),
                "gq1": str(r["Prova GQ1"])[:10],
                "gq2": str(r["Prova GQ2"])[:10],
            }
            for _, r in tabela.dropna().iterrows()
        ],
    }


# ---------- cabeçalho ----------
st.title("📚 Cronograma de Estudos")
st.caption("Informe suas disciplinas e as datas das provas. O cronograma é gerado até a véspera de cada GQ.")

# ---------- barra lateral: configuração geral ----------
with st.sidebar:
    st.header("⚙️ Configuração")
    arquivo = st.file_uploader("Carregar JSON (opcional)", type=["json"])
    inicio = st.date_input("Início dos estudos", value=date.fromisoformat(EXEMPLO["inicio"]), format="DD/MM/YYYY")
    lim_semana = st.number_input("Horas por dia (seg a sex)", min_value=0.5, max_value=16.0, value=4.0, step=0.5)
    lim_sabado = st.number_input("Horas no sábado", min_value=0.5, max_value=16.0, value=2.0, step=0.5)
    st.caption("Domingo é livre.")

# ---------- tabela de disciplinas ----------
st.subheader("1. Disciplinas")
st.caption("Clique nas células para editar. Use o + no fim da tabela para adicionar uma disciplina.")

tabela = st.data_editor(
    tabela_inicial(),
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Disciplina": st.column_config.TextColumn(required=True),
        "Dificuldade": st.column_config.NumberColumn(min_value=1, max_value=5, step=1, required=True, help="1 (fácil) a 5 (difícil)"),
        "Horas no semestre": st.column_config.NumberColumn(min_value=1.0, step=1.0, required=True),
        "Prova GQ1": st.column_config.DateColumn(format="DD/MM/YYYY", required=True),
        "Prova GQ2": st.column_config.DateColumn(format="DD/MM/YYYY", required=True),
    },
)

if arquivo is not None:
    st.info("Arquivo carregado: o cronograma abaixo usa o conteúdo do JSON, e não a tabela.")

gerar = st.button("Gerar cronograma", type="primary")

# ---------- resultado ----------
if gerar:
    try:
        bruto = json.load(arquivo) if arquivo is not None else monta_entrada(inicio, lim_semana, lim_sabado, tabela)
        cfg, plano, _ = pipeline(bruto)
    except SystemExit as e:  # erros de validação do gerador
        st.error(str(e.code))
        st.stop()
    except Exception as e:
        st.error(f"Não foi possível gerar o cronograma: {e}")
        st.stop()

    alocs = plano.alocs
    prog = progresso(cfg, alocs)

    linhas = pd.DataFrame(
        [
            {
                "Dia": a.dia,
                "Semana": DIAS[a.dia.weekday()],
                "Disciplina": a.nome,
                "Horas": a.horas,
                "Sugestão": ICONES[fase(prog(a))],
            }
            for a in alocs
        ]
    )

    resumo = pd.DataFrame(
        [
            {
                "Etapa": d.nome,
                "Prova": d.prova,
                "Horas planejadas": total_disc(alocs, d.nome),
                "Horas necessárias": d.horas,
                "Cobertura": min(total_disc(alocs, d.nome) / d.horas, 1.0),
            }
            for d in ordenar(cfg.disciplinas)
        ]
    )

    st.subheader("2. Resultado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Horas planejadas", f"{sum(a.horas for a in alocs):g} h")
    c2.metric("Dias com estudo", len({a.dia for a in alocs}))
    c3.metric("Dias livres para revisão", len(dias_livres(plano)))

    if plano.pendentes:
        st.warning(
            "Horas que não couberam no tempo disponível: "
            + ", ".join(f"{n}: {h:g} h" for n, h in plano.pendentes.items())
        )
    else:
        st.success("Todas as horas couberam no cronograma.")

    aba1, aba2, aba3 = st.tabs(["📅 Dia a dia", "📊 Resumo por etapa", "🗓️ Por semana"])

    with aba1:
        filtro = st.multiselect("Filtrar disciplina", sorted(linhas["Disciplina"].unique()))
        vista = linhas[linhas["Disciplina"].isin(filtro)] if filtro else linhas
        st.dataframe(
            vista,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Dia": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Horas": st.column_config.NumberColumn(format="%g h"),
            },
        )

    with aba2:
        st.dataframe(
            resumo,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Prova": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Horas planejadas": st.column_config.NumberColumn(format="%g h"),
                "Horas necessárias": st.column_config.NumberColumn(format="%g h"),
                "Cobertura": st.column_config.ProgressColumn(format="percent", min_value=0.0, max_value=1.0),
            },
        )

    with aba3:
        semanal = linhas.assign(
            Semana_inicio=pd.to_datetime(linhas["Dia"]).dt.to_period("W-SUN").apply(lambda p: p.start_time.date())
        ).pivot_table(index="Semana_inicio", columns="Disciplina", values="Horas", aggfunc="sum", fill_value=0)
        semanal.index.name = "Semana (início)"
        st.dataframe(semanal, use_container_width=True)
        st.bar_chart(semanal)

    st.download_button(
        "⬇️ Baixar cronograma em CSV",
        data=csv_texto(cfg, alocs),
        file_name="cronograma.csv",
        mime="text/csv",
    )