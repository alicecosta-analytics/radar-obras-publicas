"""
Fase 1 - Passo 2: limpeza, índices e log de exclusões.

Lê:    data/interim/contratos_<ANO>.parquet e data/interim/modificacoes_<ANO>.parquet
Grava: data/processed/empreitadas.parquet      (uma linha por empreitada, com flags e índices)
       data/processed/modificacoes_atos.parquet (uma linha por ato de modificação)
       data/processed/log_exclusoes.csv          (quantos contratos cada regra excluiu, por ano)

Rodar a partir da pasta do projeto:
    python src/transform.py

As regras seguem as decisões D1 a D9 do Diário da Fase 0. Nenhuma linha é apagada
da tabela final: cada regra vira uma coluna de flag, e os índices só são calculados
onde o contrato passa nas regras. Assim dá para auditar e mudar regras depois.
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
INTERIM = RAIZ / "data" / "interim"
PROCESSED = RAIZ / "data" / "processed"
INDICE_INE = RAIZ / "data" / "raw" / "ine_icchn.xls"   # D10: índice de custo de construção, base 2021

TIPO_EMPREITADA = "Empreitadas de obras públicas"   # D1
LIMITES_CPI = (0.5, 2.0)                            # D4
LIMITES_RAZAO_PRECO_MOD = (0.5, 2.0)                # mesmo critério para as modificações
LIMITES_RAZAO_PRAZO_MOD = (0.5, 5.0)                # prorrogações longas são plausíveis
PRAZO_MAXIMO_DIAS = 3650                            # D13: acima de 10 anos = erro de registo

COLUNAS_CONTRATO = [
    "idcontrato", "Ano", "tipoContrato", "tipoprocedimento", "objectoContrato",
    "adjudicante", "adjudicatarios", "CPV", "LocalExecucao",
    "precoBaseProcedimento", "precoContratual", "PrecoTotalEfetivo",
    "prazoExecucao", "dataCelebracaoContrato", "dataFechoContrato",
    "tipoFimContrato", "concorrentes", "TipoCriterioAdjudicacao",
]


# ---------------------------------------------------------------- leitura

def ler_anos(prefixo: str) -> pd.DataFrame:
    arquivos = sorted(INTERIM.glob(f"{prefixo}_*.parquet"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum {prefixo}_*.parquet em {INTERIM}. Rode o converter.py antes.")
    partes = []
    for arq in arquivos:
        df = pd.read_parquet(arq)
        df["ano_arquivo"] = int(arq.stem.split("_")[-1])
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def numero(s: pd.Series) -> pd.Series:
    """Converte para número; o que não for número vira vazio (NaN)."""
    return pd.to_numeric(s, errors="coerce")


def data(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


# ---------------------------------------------------------------- contratos

def preparar_empreitadas(contratos: pd.DataFrame) -> pd.DataFrame:
    colunas = [c for c in COLUNAS_CONTRATO if c in contratos.columns] + ["ano_arquivo"]
    e = contratos.loc[contratos["tipoContrato"] == TIPO_EMPREITADA, colunas].copy()   # D1

    for col in ["precoBaseProcedimento", "precoContratual", "PrecoTotalEfetivo", "prazoExecucao"]:
        e[col] = numero(e[col])

    # A coluna concorrentes é a lista das empresas ("NIF-nome"), uma por linha:
    # o número de concorrentes é o número de linhas não vazias.
    lista = e["concorrentes"].astype("string").str.strip()
    e["concorrentes"] = (lista.str.split("\n")
                              .apply(lambda itens: sum(1 for i in itens if i.strip()) if isinstance(itens, list) else pd.NA)
                              .astype("Int64"))
    e.loc[e["concorrentes"] == 0, "concorrentes"] = pd.NA
    for col in ["dataCelebracaoContrato", "dataFechoContrato"]:
        e[col] = data(e[col])

    # Mesmo contrato pode aparecer em mais de um arquivo anual: fica o registo mais recente
    e = e.sort_values("ano_arquivo").drop_duplicates("idcontrato", keep="last")

    # Variáveis derivadas para a análise
    e["ano_celebracao"] = e["dataCelebracaoContrato"].dt.year.fillna(e["ano_arquivo"]).astype(int)
    e["cpv_divisao"] = e["CPV"].astype("string").str.extract(r"^(\d{3})", expand=False)
    local = e["LocalExecucao"].astype("string").str.split(r"\|").str[0].str.split(",")
    e["local_pais"] = local.str[0].str.strip()
    e["local_distrito"] = local.str[1].str.strip()
    e["local_concelho"] = local.str[2].str.strip()
    return e


def aplicar_regras(e: pd.DataFrame) -> pd.DataFrame:
    dias = (e["dataFechoContrato"] - e["dataCelebracaoContrato"]).dt.days
    e["dias_ate_fecho"] = dias

    # Cada regra é uma flag (True = passa)
    e["r_tem_fecho"] = e["dataFechoContrato"].notna()                                   # D2
    e["r_efetivo_positivo"] = e["PrecoTotalEfetivo"].fillna(0) > 0                      # D2
    e["r_cumprido"] = (e["tipoFimContrato"].astype("string")
                       .str.startswith("O cumprimento").fillna(False).astype(bool))   # D3
    e["r_prazo_valido"] = e["prazoExecucao"].between(1, PRAZO_MAXIMO_DIAS)             # D13
    e["r_datas_validas"] = dias.fillna(0) > 0                                           # D4

    base_ok = e[["r_tem_fecho", "r_efetivo_positivo", "r_cumprido",
                 "r_prazo_valido", "r_datas_validas"]].all(axis=1)

    # Índice de custo (medida direta)
    cpi = e["precoContratual"] / e["PrecoTotalEfetivo"]
    e["r_cpi_no_intervalo"] = cpi.between(*LIMITES_CPI)                               # D4
    e["valido_custo"] = base_ok & e["r_cpi_no_intervalo"]
    e["CPIc"] = cpi.where(e["valido_custo"])

    # Índice de prazo até o fecho (limite superior do atraso)                          # D5
    e["valido_prazo_fecho"] = base_ok
    e["SPIc_fecho"] = (e["prazoExecucao"] / dias).where(e["valido_prazo_fecho"])
    e["atraso_dias_fecho"] = (dias - e["prazoExecucao"]).where(e["valido_prazo_fecho"])

    # Rescisões: fora dos índices, mas marcadas para análise à parte                  # D3
    e["rescindido"] = e["r_tem_fecho"] & ~e["r_cumprido"]
    return e


# ---------------------------------------------------------------- deflação (D10)

def ler_indice_ine() -> pd.Series:
    """Índice mensal de custo de construção de habitação nova (INE, base 2021 = 100).
    O arquivo do INE tem cabeçalho e notas; ficam só as linhas do fator 'Total'."""
    d = pd.read_excel(INDICE_INE, header=None, usecols=[0, 1, 2], engine="calamine",
                      names=["periodo", "fator", "indice"])
    d = d[d["fator"].eq("Total")]
    mes = pd.to_datetime(d["periodo"], format="%B %Y").dt.to_period("M")
    return pd.Series(pd.to_numeric(d["indice"]).values, index=mes).sort_index()


def deflacionar(e: pd.DataFrame) -> pd.DataFrame:
    """Preço contratual a preços de 2021, pelo índice do mês de celebração.
    Usado só como variável de porte; os índices CPIc e SPIc não são deflacionados (D10).
    Sem mês de celebração, ou mês além do último publicado: usa a média do ano ou o último índice."""
    if not INDICE_INE.exists():
        print(f"  Aviso: {INDICE_INE.name} não encontrado; preço deflacionado não calculado.")
        e["preco_contratual_2021"] = pd.NA
        return e
    indice = ler_indice_ine()
    media_ano = indice.groupby(indice.index.year).mean()

    mes = e["dataCelebracaoContrato"].dt.to_period("M")
    fator = mes.map(indice)
    fator = fator.fillna(e["ano_celebracao"].map(media_ano))     # mês sem índice: média do ano
    fator = fator.fillna(indice.iloc[-1])                         # ano sem índice: último publicado
    e["indice_ine"] = fator.astype(float)
    e["preco_contratual_2021"] = e["precoContratual"] * 100 / e["indice_ine"]
    print(f"  Preço deflacionado com o índice do INE ({indice.index.min()} a {indice.index.max()})")
    return e


# ---------------------------------------------------------------- modificações

def preparar_modificacoes(mod: pd.DataFrame) -> pd.DataFrame:
    m = mod.copy()
    m["modifContratoData"] = data(m["modifContratoData"])
    m["modifContratoPrecoAlterado"] = numero(m["modifContratoPrecoAlterado"])
    m["modifPrazoExecucao"] = numero(m["modifPrazoExecucao"])
    m["modifContratoFundamento"] = m["modifContratoFundamento"].astype("string")

    chave = ["idcontrato", "modifContratoData", "modifContratoPrecoAlterado", "modifPrazoExecucao"]

    # D9: cada linha é um fundamento; junta os fundamentos do mesmo ato
    atos = (m.groupby(chave, dropna=False)
              .agg(fundamentos=("modifContratoFundamento",
                                lambda s: " | ".join(sorted(set(s.dropna())))))
              .reset_index())

    f = atos["fundamentos"].str.lower()
    atos["causa_trab_complementares"] = f.str.contains("complementares")
    atos["causa_trab_a_menos"] = f.str.contains("a menos")
    atos["causa_revisao_ordinaria"] = f.str.contains("revisão ordinária")
    atos["causa_crise_precos"] = f.str.contains("36/2022|anormal e imprevis", regex=True)
    atos["causa_interesse_publico"] = f.str.contains("interesse público")
    atos["causa_prorrogacao"] = f.str.contains("prorrogação")
    return atos


def resumir_por_contrato(atos: pd.DataFrame) -> pd.DataFrame:
    ordenado = atos.sort_values(["idcontrato", "modifContratoData"])
    causas = [c for c in atos.columns if c.startswith("causa_")]
    resumo = ordenado.groupby("idcontrato").agg(
        n_atos=("modifContratoData", "size"),
        preco_final_mod=("modifContratoPrecoAlterado", "last"),   # D9: estado final = último ato
        prazo_final_mod=("modifPrazoExecucao", "last"),
        data_ultima_mod=("modifContratoData", "last"),
        **{c: (c, "any") for c in causas},
    )
    return resumo.reset_index()


def juntar_modificacoes(e: pd.DataFrame, resumo: pd.DataFrame) -> pd.DataFrame:
    e = e.merge(resumo, on="idcontrato", how="left")
    e["modificado"] = e["n_atos"].notna()
    e["n_atos"] = e["n_atos"].fillna(0).astype(int)
    for c in [c for c in resumo.columns if c.startswith("causa_")]:
        e[c] = e[c].fillna(False).astype(bool)

    razao_preco = e["preco_final_mod"] / e["precoContratual"]
    razao_prazo = e["prazo_final_mod"] / e["prazoExecucao"]
    e["r_mod_preco_valido"] = razao_preco.between(*LIMITES_RAZAO_PRECO_MOD)
    e["r_mod_prazo_valido"] = razao_prazo.between(*LIMITES_RAZAO_PRAZO_MOD)

    # D8: limite inferior do custo (preço final da última modificação)
    e["CPIc_mod"] = (e["precoContratual"] / e["preco_final_mod"]).where(e["r_mod_preco_valido"])
    # D7: limite inferior do atraso (prorrogação formal)
    e["SPIc_formal"] = (e["prazoExecucao"] / e["prazo_final_mod"]).where(e["r_mod_prazo_valido"])
    e["prorrogacao_dias"] = (e["prazo_final_mod"] - e["prazoExecucao"]).where(e["r_mod_prazo_valido"])
    return e


# ---------------------------------------------------------------- log

def log_exclusoes(e: pd.DataFrame) -> pd.DataFrame:
    g = e.groupby("ano_celebracao")
    log = pd.DataFrame({
        "empreitadas": g.size(),
        "sem_fecho": g["r_tem_fecho"].apply(lambda s: (~s).sum()),
        "efetivo_zero_ou_vazio": g["r_efetivo_positivo"].apply(lambda s: (~s).sum()),
        "nao_cumprido": g.apply(lambda d: (d["r_tem_fecho"] & ~d["r_cumprido"]).sum(), include_groups=False),
        "prazo_invalido": g["r_prazo_valido"].apply(lambda s: (~s).sum()),
        "datas_invalidas": g.apply(lambda d: (d["r_tem_fecho"] & ~d["r_datas_validas"]).sum(), include_groups=False),
        "validos_prazo_fecho": g["valido_prazo_fecho"].sum(),
        "cpi_fora_do_intervalo": g.apply(lambda d: (d["valido_prazo_fecho"] & ~d["r_cpi_no_intervalo"]).sum(), include_groups=False),
        "validos_custo": g["valido_custo"].sum(),
        "modificados": g["modificado"].sum(),
        "com_CPIc_mod": g["CPIc_mod"].count(),
        "com_SPIc_formal": g["SPIc_formal"].count(),
    })
    return log.reset_index()


# ---------------------------------------------------------------- execução

def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)

    print("Lendo contratos...")
    e = preparar_empreitadas(ler_anos("contratos"))
    e = aplicar_regras(e)
    e = deflacionar(e)
    print(f"  {len(e):,} empreitadas")

    print("Lendo modificações...")
    atos = preparar_modificacoes(ler_anos("modificacoes"))
    print(f"  {len(atos):,} atos de modificação")

    e = juntar_modificacoes(e, resumir_por_contrato(atos))

    e.to_parquet(PROCESSED / "empreitadas.parquet", index=False)
    atos.to_parquet(PROCESSED / "modificacoes_atos.parquet", index=False)
    log = log_exclusoes(e)
    log.to_csv(PROCESSED / "log_exclusoes.csv", index=False, sep=";", encoding="utf-8-sig")

    print("\nLog de exclusões (por ano de celebração):")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(log.to_string(index=False))

    janela = e[e["ano_celebracao"].between(2019, 2022)]
    print("\nResumo da janela 2019-2022:")
    print(f"  CPIc válidos: {janela['CPIc'].count():,} | mediana {janela['CPIc'].median():.2f} "
          f"| estouro {(janela['CPIc'] < 1).sum() / janela['CPIc'].count():.0%}")
    print(f"  SPIc_fecho válidos: {janela['SPIc_fecho'].count():,} | mediana {janela['SPIc_fecho'].median():.2f}")
    print(f"  SPIc_formal (só modificados): {janela['SPIc_formal'].count():,} "
          f"| mediana {janela['SPIc_formal'].median():.2f}")
    print("\nConcluído. Arquivos em data/processed/")


if __name__ == "__main__":
    main()
