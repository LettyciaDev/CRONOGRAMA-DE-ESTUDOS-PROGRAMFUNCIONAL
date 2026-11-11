# Cronograma de Estudos (Programação Funcional)

Gerador de cronograma de estudos por período (semestre), escrito em Python seguindo os preceitos da programação funcional: só `lambda`, tuplas imutáveis (`namedtuple`), composição de funções e `reduce`. Não há `def`, `class` nem laços como instrução. O `for` aparece apenas dentro de comprehensions.

## Alunas:
- Anna Beatriz dos Santos Silva - 00000851757
- Lettycia de Melo França - 00000853771

## O que o programa faz

A partir de uma data de início, de limites de horas por dia e de uma lista de disciplinas, o programa monta um plano de estudos até a véspera de cada prova.

- Cada disciplina tem duas etapas: **GQ1** e **GQ2**.
- As horas totais da disciplina no semestre são divididas meio a meio entre as duas etapas.
- A etapa GQ1 vai do início até a véspera da prova do GQ1. A etapa GQ2 começa no dia seguinte ao GQ1 e vai até a véspera da prova do GQ2.
- Estuda-se de **segunda a sexta** (limite normal), no **sábado** (limite menor) e o **domingo** é livre.
- Em cada dia, a etapa com prova mais próxima entra primeiro. Em caso de empate, a disciplina mais difícil vem antes.
- Cada sessão recebe uma sugestão conforme o progresso na etapa:
  - até 50% do material: **teoria**
  - de 50% a 85%: **lista**
  - acima de 85%: **revisão**
- Se alguma hora não couber no tempo disponível, o relatório mostra um aviso com as horas pendentes.

## Como executar

Requer apenas Python 3 (nenhuma biblioteca externa).

```bash
# usa o exemplo embutido no código
python gerador_cronograma.py

# usa um arquivo JSON de entrada
python gerador_cronograma.py entrada.json

# além do relatório, salva o plano em CSV
python gerador_cronograma.py entrada.json --csv plano.csv
```

## Formato do `entrada.json`

```json
{
  "inicio": "2027-02-22",
  "limite_semana": 4,
  "limite_sabado": 2,
  "disciplinas": [
    {
      "nome": "Ciência de Dados",
      "dificuldade": 4,
      "horas": 45,
      "gq1": "2027-04-10",
      "gq2": "2027-06-12"
    }
  ]
}
```

| Campo | Significado |
| --- | --- |
| `inicio` | Primeiro dia de estudo (`AAAA-MM-DD` ou `DD/MM/AAAA`) |
| `limite_semana` | Horas máximas por dia, de segunda a sexta |
| `limite_sabado` | Horas máximas no sábado |
| `nome` | Nome da disciplina |
| `dificuldade` | De 1 a 5, desempata a prioridade |
| `horas` | Total de horas de estudo da disciplina no semestre |
| `gq1`, `gq2` | Datas das provas do 1º e do 2º GQ |

A entrada é validada: dificuldade entre 1 e 5, horas e limites maiores que zero e prova depois do início do estudo.

## Saída

- **Relatório em texto:** tabela dia a dia (disciplina, horas e sugestão), resumo por etapa, total de horas, quantidade de dias sem alocação e aviso de horas pendentes, se houver.
- **CSV (opcional):** colunas `dia,disciplina,horas,sugestao`.

## Estrutura do código

O código está organizado em 8 partes, todas funções puras, exceto a última:

1. Imports, tipos imutáveis e utilitários
2. Entrada: conversão, validação e exemplo
3. Ordenação, dias de estudo e limite por dia
4. Alocar uma disciplina em um dia (`passo_disc`)
5. Preencher os dias e gerar o plano (`aloca_dia`, `planejar`)
6. Relatório em texto
7. CSV e `pipeline`
8. Bordas: leitura do arquivo, impressão e gravação (únicos efeitos colaterais)

## Interface (opcional)

O arquivo `interface.py` é uma interface web simples em Streamlit, separada do gerador. Ela apenas chama o `pipeline` e o `csv_texto`. Não é necessária para usar o programa.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run interface.py
```

Na página é possível editar o JSON, carregar um arquivo, gerar o cronograma e baixar o CSV.
