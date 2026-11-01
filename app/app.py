"""
Radar de Desvios de Custo e Prazo em Obras Públicas — painel interativo.

Rodar localmente, a partir da pasta do projeto:
    streamlit run app/app.py

Dados: app/dados/, gerados por src/exportar_painel.py a partir dos dados abertos do Portal Base.
"""

from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

DADOS = Path(__file__).parent / "dados"
REPO = "https://github.com/alicecosta-analytics/radar-obras-publicas"
LINK_BASE = "https://www.base.gov.pt/Base4/pt/detalhe/?type=contratos&id={}"

# Paleta de referência validada (azul, laranja, verde-água) e tons neutros
AZUL, LARANJA, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
CINZA = "#52514e"
COR_PROC = {"Ajuste direto": AQUA, "Consulta prévia": LARANJA, "Concurso público": AZUL, "Outros": "#9a9893"}
MIN_GRUPO = 50

st.set_page_config(page_title="Radar de Obras Públicas", page_icon="🏗️", layout="wide")


# ---------------------------------------------------------------- dados

@st.cache_data
def carregar():
    p = pd.read_parquet(DADOS / "painel.parquet")
    p["link"] = p["id"].map(LINK_BASE.format)
    efeitos = pd.read_csv(DADOS / "efeitos_modelo.csv") if (DADOS / "efeitos_modelo.csv").exists() else None
    robustez = pd.read_csv(DADOS / "robustez.csv") if (DADOS / "robustez.csv").exists() else None
    return p, efeitos, robustez


def wilson(sucessos, n, z=1.96):
    """Percentagem e intervalo de confiança de 95% (Wilson)."""
    sucessos, n = np.asarray(sucessos, float), np.asarray(n, float)
    p = np.divide(sucessos, n, out=np.zeros_like(n), where=n > 0)
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    meia = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return 100 * p, 100 * (centro - meia), 100 * (centro + meia)


def pct(x):
    return f"{x:.1f}%".replace(".", ",")


def num(x):
    return f"{x:,.0f}".replace(",", ".")


def euros(x):
    if x >= 1e6:
        return f"{x / 1e6:.1f} M€".replace(".", ",")
    return f"{x / 1e3:.0f} mil €"


def resumo_estouro(df, grupo):
    v = df[df["estouro"].notna()]
    g = v.groupby(grupo, observed=True).agg(n=("estouro", "size"), estouros=("estouro", "sum")).reset_index()
    g["pct"], g["ic_inf"], g["ic_sup"] = wilson(g["estouros"], g["n"])
    return g


painel, efeitos, robustez = carregar()

# ---------------------------------------------------------------- filtros

st.sidebar.header("Filtros")
anos = st.sidebar.slider("Ano de celebração", int(painel["ano"].min()), int(painel["ano"].max()), (2019, 2022))
st.sidebar.caption("A janela principal da análise é 2019–2022. Em 2018 o registo do fecho ainda era irregular; "
                   "em 2023 muitas obras ainda não tinham terminado.")


def multiselecao(rotulo, coluna):
    opcoes = sorted(painel[coluna].dropna().unique())
    escolha = st.sidebar.multiselect(rotulo, opcoes, placeholder="Todos")
    return escolha or opcoes


procs = multiselecao("Procedimento", "procedimento")
faixas = multiselecao("Faixa de preço contratual", "faixa_porte")
tipos = multiselecao("Tipo de obra (CPV)", "tipo_obra")
distritos = multiselecao("Distrito", "distrito")

f = painel[painel["ano"].between(*anos) & painel["procedimento"].isin(procs) & painel["faixa_porte"].isin(faixas)
           & painel["tipo_obra"].isin(tipos) & painel["distrito"].isin(distritos)]
custo = f[f["estouro"].notna()]

st.sidebar.divider()
st.sidebar.markdown(f"**{num(len(f))}** empreitadas selecionadas  \n**{num(len(custo))}** com índice de custo válido")
st.sidebar.markdown(f"[Código e método no GitHub]({REPO})")

# ---------------------------------------------------------------- cabeçalho

st.title("Radar de Desvios em Obras Públicas")
st.markdown("Quanto as empreitadas de obras públicas em Portugal se afastam do **preço** e do **prazo** "
            "contratados, e o que explica esses desvios. Dados abertos do Portal Base (IMPIC).")

if custo.empty:
    st.warning("Nenhum contrato com índice de custo válido para os filtros escolhidos.")
    st.stop()

aba_geral, aba_grupos, aba_prazo, aba_modelo, aba_metodo = st.tabs(
    ["Visão geral", "Comparar grupos", "Prazo", "O que explica o estouro", "Método e limitações"])

# ---------------------------------------------------------------- visão geral

with aba_geral:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Contratos com índice de custo", num(len(custo)))
    k2.metric("Com estouro de custo", pct(100 * custo["estouro"].mean()))
    k3.metric("Terminaram no preço contratado", pct(100 * (custo["cpi"] == 1).mean()))
    k4.metric("Estouro mediano, quando há estouro", pct(custo.loc[custo["estouro"], "desvio_pct"].median()))

    st.subheader("Percentagem de obras com estouro de custo, por ano")
    por_ano = resumo_estouro(f, "ano")
    base = alt.Chart(por_ano).encode(x=alt.X("ano:O", title="Ano de celebração", axis=alt.Axis(labelAngle=0)))
    tooltip = [alt.Tooltip("ano:O", title="Ano"), alt.Tooltip("pct:Q", title="% com estouro", format=".1f"),
               alt.Tooltip("ic_inf:Q", title="IC 95% inferior", format=".1f"),
               alt.Tooltip("ic_sup:Q", title="IC 95% superior", format=".1f"),
               alt.Tooltip("n:Q", title="Contratos", format=",")]
    grafico = (base.mark_rule(color=AZUL, strokeWidth=1.5).encode(y="ic_inf:Q", y2="ic_sup:Q")
               + base.mark_line(color=AZUL, strokeWidth=2).encode(
                   y=alt.Y("pct:Q", title="% com estouro", scale=alt.Scale(domain=[0, max(50, por_ano["ic_sup"].max() + 5)])))
               + base.mark_point(color=AZUL, filled=True, size=90, stroke="white", strokeWidth=2)
                   .encode(y="pct:Q", tooltip=tooltip))
    st.altair_chart(grafico.properties(height=320), width="stretch")
    st.caption("A barra vertical em cada ano é o intervalo de confiança de 95%. Passe o mouse sobre os pontos para ver os valores.")

    st.subheader("Distribuição do desvio de custo")
    hist = custo.assign(desvio=custo["desvio_pct"].clip(-40, 60))
    st.altair_chart(
        alt.Chart(hist).mark_bar(color=AZUL, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("desvio:Q", bin=alt.Bin(step=2.5, extent=[-40, 62.5]),
                    title="Desvio de custo (%) ← economia | estouro →", axis=alt.Axis(format=".0f")),
            y=alt.Y("count():Q", title="Contratos", axis=alt.Axis(labelExpr="replace(format(datum.value, ',.0f'), /,/g, '.')")),
            tooltip=[alt.Tooltip("desvio:Q", bin=alt.Bin(step=2.5, extent=[-40, 62.5]), title="Faixa de desvio (%)"),
                     alt.Tooltip("count():Q", title="Contratos", format=",")]).properties(height=280),
        width="stretch")
    st.caption("Valores abaixo de −40% e acima de +60% juntados nas pontas.")

    st.subheader("Maiores estouros de custo")
    top = (custo.nlargest(50, "desvio_pct")
           [["ano", "entidade", "objeto", "procedimento", "preco", "desvio_pct", "link"]])
    st.dataframe(top, hide_index=True, width="stretch", column_config={
        "ano": st.column_config.NumberColumn("Ano", format="%d"),
        "entidade": "Entidade", "objeto": "Objeto do contrato", "procedimento": "Procedimento",
        "preco": st.column_config.NumberColumn("Preço contratual (€)", format="localized"),
        "desvio_pct": st.column_config.NumberColumn("Estouro (%)", format="%.1f"),
        "link": st.column_config.LinkColumn("Portal Base", display_text="abrir"),
    })
    st.caption("O índice de custo exclui desvios acima de +100% e abaixo de −50% (prováveis erros de registo).")

# ---------------------------------------------------------------- comparar grupos

with aba_grupos:
    dimensoes = {"Procedimento": "procedimento", "Faixa de preço contratual": "faixa_porte",
                 "Tipo de obra (CPV)": "tipo_obra", "Distrito": "distrito"}
    escolha = st.radio("Comparar por", list(dimensoes), horizontal=True)
    col = dimensoes[escolha]
    g = resumo_estouro(f, col)
    g = g[g["n"] >= MIN_GRUPO]
    ordem = sorted(g[col]) if col == "faixa_porte" else g.sort_values("pct", ascending=False)[col].tolist()
    base = alt.Chart(g).encode(y=alt.Y(f"{col}:N", sort=ordem, title=None, axis=alt.Axis(labelLimit=260)))
    tooltip = [alt.Tooltip(f"{col}:N", title=escolha), alt.Tooltip("pct:Q", title="% com estouro", format=".1f"),
               alt.Tooltip("ic_inf:Q", title="IC 95% inferior", format=".1f"),
               alt.Tooltip("ic_sup:Q", title="IC 95% superior", format=".1f"),
               alt.Tooltip("n:Q", title="Contratos", format=",")]
    barras = base.mark_bar(color=AZUL, cornerRadiusEnd=4, height={"band": 0.6}).encode(
        x=alt.X("pct:Q", title="% com estouro de custo", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(tickCount=5)), tooltip=tooltip)
    erros = base.mark_rule(color=CINZA).encode(x="ic_inf:Q", x2="ic_sup:Q")
    st.altair_chart((barras + erros).properties(height=max(180, 34 * len(g))), width="stretch")
    st.caption(f"Só grupos com pelo menos {MIN_GRUPO} contratos com índice válido. A linha cinzenta é o IC de 95%.")

    st.subheader("Procedimento dentro de cada faixa de porte")
    st.markdown("O concurso público concentra as obras grandes. Comparar dentro da mesma faixa separa o efeito do "
                "procedimento do efeito do tamanho.")
    cruz = resumo_estouro(f, ["faixa_porte", "procedimento"])
    cruz = cruz[(cruz["n"] >= MIN_GRUPO) & (cruz["procedimento"] != "Outros")]
    st.altair_chart(
        alt.Chart(cruz).mark_bar(cornerRadiusEnd=3).encode(
            x=alt.X("faixa_porte:N", title="Faixa de preço contratual", axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("procedimento:N", sort=list(COR_PROC)),
            y=alt.Y("pct:Q", title="% com estouro", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("procedimento:N", title="Procedimento", sort=list(COR_PROC),
                            scale=alt.Scale(domain=list(COR_PROC)[:3], range=[COR_PROC[k] for k in list(COR_PROC)[:3]])),
            tooltip=[alt.Tooltip("faixa_porte:N", title="Faixa"), alt.Tooltip("procedimento:N", title="Procedimento"),
                     alt.Tooltip("pct:Q", title="% com estouro", format=".1f"),
                     alt.Tooltip("n:Q", title="Contratos", format=",")]).properties(height=320),
        width="stretch")

# ---------------------------------------------------------------- prazo

with aba_prazo:
    st.markdown("Os dados abertos não registam a data real de conclusão da obra. Por isso o atraso é medido "
                "por duas aproximações, uma de cada lado do valor real:")
    st.markdown("- **Limite inferior:** contratos com **prorrogação formal** de prazo (base de modificações).\n"
                "- **Limite superior:** contratos **fechados no Portal depois do fim do prazo**; inclui o tempo "
                "administrativo entre o fim da obra e o fecho do contrato.")
    pz = f[f["apos_prazo"].notna()]
    if pz.empty:
        st.info("Sem contratos com dados de prazo para os filtros escolhidos.")
    else:
        por_ano = pz.groupby("ano").agg(formal=("prorrogado", "mean"), fecho=("apos_prazo", "mean"),
                                        n=("ano", "size")).reset_index()
        por_ano[["formal", "fecho"]] *= 100
        longo = por_ano.melt(["ano", "n"], ["fecho", "formal"], var_name="medida", value_name="pct")
        longo["medida"] = longo["medida"].map({"fecho": "Fechados após o prazo (limite superior)",
                                               "formal": "Com prorrogação formal (limite inferior)"})
        faixa = alt.Chart(por_ano).mark_area(color=AZUL, opacity=0.1).encode(
            x="ano:O", y="formal:Q", y2="fecho:Q")
        linhas = alt.Chart(longo).mark_line(point=alt.OverlayMarkDef(size=80, filled=True), strokeWidth=2).encode(
            x=alt.X("ano:O", title="Ano de celebração", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("pct:Q", title="% de contratos", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("medida:N", title=None,
                            scale=alt.Scale(domain=["Fechados após o prazo (limite superior)",
                                                    "Com prorrogação formal (limite inferior)"],
                                            range=[AZUL, LARANJA]),
                            legend=alt.Legend(orient="top", labelLimit=400)),
            tooltip=[alt.Tooltip("ano:O", title="Ano"), alt.Tooltip("medida:N", title="Medida"),
                     alt.Tooltip("pct:Q", title="%", format=".1f"), alt.Tooltip("n:Q", title="Contratos", format=",")])
        st.altair_chart((faixa + linhas).properties(height=340), width="stretch")
        ult = por_ano.iloc[-1]
        st.markdown(f"Em {int(ult['ano'])}, entre **{pct(ult['formal'])}** e **{pct(ult['fecho'])}** das obras "
                    "excederam o prazo. A faixa larga é, em si, um achado: os dados abertos não permitem "
                    "saber com precisão quantas obras atrasaram.")

# ---------------------------------------------------------------- modelo

with aba_modelo:
    st.markdown("Uma **regressão logística** estima o efeito de cada fator na probabilidade de estouro "
                "**mantendo os outros constantes**: porte, prazo, procedimento, tipo de obra, distrito, ano e "
                "número de concorrentes. Empreitadas de 2019 a 2022; erros-padrão agrupados por entidade adjudicante.")
    st.caption("Estes resultados vêm do modelo completo e não mudam com os filtros da lateral.")
    if efeitos is None:
        st.info("Rode os notebooks 05 e 06 e o script de exportação para mostrar os resultados do modelo.")
    else:
        ef = efeitos.rename(columns={efeitos.columns[0]: "variavel"})
        rotulos = {"log_preco": "Preço contratual 10× maior", "log_prazo": "Prazo contratual 10× maior",
                   "procedimento: Concurso público": "Concurso público (vs. ajuste direto)",
                   "procedimento: Consulta prévia": "Consulta prévia (vs. ajuste direto)",
                   "ano: 2020": "Celebrado em 2020 (vs. 2019)", "ano: 2021": "Celebrado em 2021 (vs. 2019)",
                   "ano: 2022": "Celebrado em 2022 (vs. 2019)",
                   "concorrencia: 6 ou mais": "6 ou mais concorrentes (vs. 1)"}
        ef = ef[ef["variavel"].isin(rotulos)].assign(rotulo=lambda d: d["variavel"].map(rotulos))
        ef.columns = ["variavel", "efeito", "ic_inf", "ic_sup", "rotulo"]
        ordem = ef.sort_values("efeito", ascending=False)["rotulo"].tolist()
        base = alt.Chart(ef).encode(y=alt.Y("rotulo:N", sort=ordem, title=None, axis=alt.Axis(labelLimit=320)))
        tooltip = [alt.Tooltip("rotulo:N", title="Fator"), alt.Tooltip("efeito:Q", title="Efeito (p.p.)", format="+.1f"),
                   alt.Tooltip("ic_inf:Q", title="IC 95% inferior", format="+.1f"),
                   alt.Tooltip("ic_sup:Q", title="IC 95% superior", format="+.1f")]
        st.altair_chart(
            (alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=CINZA, strokeDash=[4, 4]).encode(x="x:Q")
             + base.mark_rule(color=AZUL, strokeWidth=2).encode(x="ic_inf:Q", x2="ic_sup:Q")
             + base.mark_point(color=AZUL, filled=True, size=100, stroke="white", strokeWidth=2).encode(
                 x=alt.X("efeito:Q", title="Efeito na probabilidade de estouro (pontos percentuais)", axis=alt.Axis(tickCount=8)),
                 tooltip=tooltip)).properties(height=320),
            width="stretch")
        st.markdown("**Como ler:** um contrato de concurso público tem, em média, alguns pontos percentuais a mais "
                    "de probabilidade de estouro que um ajuste direto do **mesmo porte, ano, tipo de obra e distrito**. "
                    "A linha horizontal é o intervalo de confiança de 95%: se não cruza o zero, o efeito é significativo.")

    if robustez is not None:
        with st.expander("Os resultados resistem a outras escolhas de método?"):
            r = robustez.copy()
            r.columns = [c.strip() for c in r.columns]
            st.dataframe(r[["variação", "efeito", "p.p.", "IC 2,5%", "IC 97,5%", "contratos"]],
                         hide_index=True, width="stretch")
            st.caption("O efeito do concurso público e o de 2021 foram reestimados mudando uma escolha de método "
                       "de cada vez. Ficam positivos e significativos em todas as variações.")

# ---------------------------------------------------------------- método

with aba_metodo:
    st.markdown(f"""
**Fonte.** Contratos e modificações contratuais registados no Portal Base pelas entidades adjudicantes,
publicados pelo IMPIC em dados abertos (dados.gov.pt). Índice de custo de construção do INE para a deflação.

**Índice de custo (CPIc).** Inspirado na Gestão do Valor Agregado: preço contratual ÷ preço total efetivo.
Abaixo de 1 = estouro. Calculado só para contratos com fecho registado, terminados por cumprimento e com
valores plausíveis.

**Principais limitações**
- Só cerca de 45% das empreitadas têm o fecho registado; o registo melhora ao longo dos anos.
- A data de fecho no Portal inclui tempo administrativo depois do fim da obra, o que exagera o atraso.
- Os dados são declarados pelas próprias entidades, sem auditoria campo a campo.
- A regressão mostra associação, não causa.

O método completo, as decisões de limpeza e o código estão no [repositório do projeto]({REPO}).
""")
