"""
Fase 4: prepara os dados do painel.

Lê:    data/processed/empreitadas.parquet
       reports/regressao_efeitos_marginais.csv e reports/robustez_efeitos.csv (notebooks 05 e 06)
Grava: app/dados/painel.parquet (empreitadas de 2018 a 2023, só as colunas que o painel usa)
       app/dados/efeitos_modelo.csv e app/dados/robustez.csv

Rodar a partir da pasta do projeto, depois do transform.py e dos notebooks 05 e 06:
    python src/exportar_painel.py

Os arquivos de app/dados vão para o GitHub: o painel publicado precisa deles.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PROCESSED = RAIZ / "data" / "processed"
REPORTS = RAIZ / "reports"
SAIDA = RAIZ / "app" / "dados"

ANOS = (2018, 2023)
PROCEDIMENTOS = {"Ajuste Direto Regime Geral": "Ajuste direto",
                 "Consulta Prévia": "Consulta prévia",
                 "Concurso público": "Concurso público"}
TIPOS_OBRA = {"450": "Construção (geral)", "451": "Preparação de terrenos",
              "452": "Edifícios e engenharia civil", "453": "Instalações em edifícios",
              "454": "Acabamentos", "455": "Aluguer de equipamento"}
FAIXAS = [0, 150_000, 1_000_000, 5_000_000, np.inf]
ROTULOS_FAIXA = ["1. até 150 mil €", "2. 150 mil a 1 M€", "3. 1 a 5 M€", "4. acima de 5 M€"]
CAUSAS = ["causa_trab_complementares", "causa_trab_a_menos", "causa_revisao_ordinaria",
          "causa_crise_precos", "causa_interesse_publico", "causa_prorrogacao"]


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    e = pd.read_parquet(PROCESSED / "empreitadas.parquet")
    e = e[e["ano_celebracao"].between(*ANOS)].copy()

    entidade = e["adjudicante"].astype("string").str.replace(r"^\d{9}\s*-\s*", "", regex=True)
    estouro = (e["CPIc"] < 1).where(e["CPIc"].notna())
    painel = pd.DataFrame({
        "id": e["idcontrato"].astype("int64"),
        "ano": e["ano_celebracao"].astype(int),
        "procedimento": e["tipoprocedimento"].map(PROCEDIMENTOS).fillna("Outros"),
        "faixa_porte": pd.cut(e["precoContratual"], FAIXAS, labels=ROTULOS_FAIXA).astype("string"),
        "tipo_obra": e["cpv_divisao"].map(TIPOS_OBRA).fillna("Outros"),
        "distrito": e["local_distrito"].astype("string").fillna("Não informado"),
        "entidade": entidade,
        "objeto": e["objectoContrato"].astype("string").str.slice(0, 160),
        "concorrentes": e["concorrentes"].astype("Int64"),
        "preco": e["precoContratual"].astype(float),
        "preco_2021": e["preco_contratual_2021"].astype(float),
        "cpi": e["CPIc"].astype(float),
        "desvio_pct": ((1 / e["CPIc"] - 1) * 100).astype(float),
        "estouro": estouro.astype("boolean"),
        "apos_prazo": (e["SPIc_fecho"] < 1).where(e["SPIc_fecho"].notna()).astype("boolean"),
        "prorrogado": ((e["prorrogacao_dias"].fillna(0) > 0)
                       .where(e["valido_prazo_fecho"].fillna(False).astype(bool))).astype("boolean"),
        "modificado": e["modificado"].fillna(False).astype(bool),
        **{c.replace("causa_", "causa_"): e[c].fillna(False).astype(bool) for c in CAUSAS},
    })
    painel.to_parquet(SAIDA / "painel.parquet", index=False)
    print(f"painel.parquet: {len(painel):,} empreitadas de {ANOS[0]} a {ANOS[1]}, "
          f"{(SAIDA / 'painel.parquet').stat().st_size / 1e6:.1f} MB")

    for origem, destino in [("regressao_efeitos_marginais.csv", "efeitos_modelo.csv"),
                            ("robustez_efeitos.csv", "robustez.csv")]:
        arq = REPORTS / origem
        if arq.exists():
            pd.read_csv(arq, sep=";", decimal=",", encoding="utf-8-sig").to_csv(SAIDA / destino, index=False)
            print(f"{destino}: copiado de reports/{origem}")
        else:
            print(f"Aviso: reports/{origem} não encontrado (rode os notebooks 05 e 06)")


if __name__ == "__main__":
    main()
