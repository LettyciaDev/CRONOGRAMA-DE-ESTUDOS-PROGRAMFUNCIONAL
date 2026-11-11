import json

import streamlit as st

from gerador_cronograma import EXEMPLO, csv_texto, pipeline

st.set_page_config(page_title="Gerador de Cronograma de Estudos", layout="wide")

st.title("Gerador de Cronograma de Estudos")
st.write("Insira a configuração em formato JSON abaixo ou utilize o exemplo padrão para gerar seu cronograma.")

with st.sidebar:
    st.header("Configuração")
    arquivo_up = st.file_uploader("Carregar arquivo JSON", type=["json"])
    st.markdown("---")
    st.info("O JSON deve conter as chaves `inicio`, `limite_semana`, `limite_sabado` e a lista de `disciplinas`.")

if arquivo_up is not None:
    try:
        conteudo_json = json.load(arquivo_up)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo JSON: {e}")
        conteudo_json = EXEMPLO
else:
    conteudo_json = EXEMPLO

json_str = st.text_area("JSON de Configuração", value=json.dumps(conteudo_json, indent=4, ensure_ascii=False), height=350)

if st.button("Gerar Cronograma", type="primary"):
    try:
        cfg, plano, texto_relatorio = pipeline(json.loads(json_str))
        st.success("Cronograma gerado com sucesso!")
        st.text(texto_relatorio)
        st.download_button(
            label="Baixar Cronograma em CSV",
            data=csv_texto(cfg, plano.alocs),
            file_name="cronograma.csv",
            mime="text/csv",
        )
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o cronograma: {e}")