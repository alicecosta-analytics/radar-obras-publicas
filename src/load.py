"""
Fase 2 - Passo 1: carrega os dados processados num banco SQLite.

Lê:    data/processed/empreitadas.parquet e data/processed/modificacoes_atos.parquet
       sql/schema.sql (estrutura das tabelas)
Grava: data/obras.db

Rodar a partir da pasta do projeto, depois do transform.py:
    python src/load.py

O banco é recriado do zero a cada execução.
"""

import sqlite3
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PROCESSED = RAIZ / "data" / "processed"
SCHEMA = RAIZ / "sql" / "schema.sql"
BANCO = RAIZ / "data" / "obras.db"

CAUSAS = ["causa_trab_complementares", "causa_trab_a_menos", "causa_revisao_ordinaria",
          "causa_crise_precos", "causa_interesse_publico", "causa_prorrogacao"]


def texto_data(s: pd.Series) -> pd.Series:
    """Data -> texto AAAA-MM-DD (vazio continua vazio)."""
    return pd.to_datetime(s, errors="coerce").dt.strftime("%Y-%m-%d")


def inteiro01(s: pd.Series) -> pd.Series:
    return s.fillna(False).astype(bool).astype(int)


def dimensao(valores: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Tabela de valores distintos com uma chave numérica sequencial."""
    d = valores.drop_duplicates().reset_index(drop=True)
    d.insert(0, id_col, range(1, len(d) + 1))
    return d


def montar_dimensoes(e: pd.DataFrame) -> dict:
    # Entidade: "503278602 - Metro do Porto, S. A." -> NIF + nome.
    # O mesmo NIF aparece com grafias diferentes; fica a grafia mais frequente.
    # Sem NIF no texto, o próprio nome serve de chave.
    adj = e["adjudicante"].astype("string").str.strip()
    partes = adj.str.extract(r"^(\d{9})\s*-\s*(.+)$")
    e["nif"] = partes[0].fillna(adj)
    e["nome_entidade"] = partes[1].str.strip().fillna(adj)
    nomes = (e.groupby("nif")["nome_entidade"]
               .agg(lambda s: s.value_counts().index[0])
               .reset_index()
               .rename(columns={"nome_entidade": "nome"}))
    dim_entidade = dimensao(nomes, "id_entidade")

    dim_procedimento = dimensao(
        e[["tipoprocedimento"]].dropna().rename(columns={"tipoprocedimento": "tipo"}),
        "id_procedimento")

    dim_local = dimensao(
        e[["local_pais", "local_distrito", "local_concelho"]].dropna(how="all")
         .rename(columns={"local_pais": "pais", "local_distrito": "distrito",
                          "local_concelho": "concelho"}),
        "id_local")

    dim_cpv = dimensao(e[["cpv_divisao"]].dropna(), "id_cpv")

    return {"dim_entidade": dim_entidade, "dim_procedimento": dim_procedimento,
            "dim_local": dim_local, "dim_cpv": dim_cpv}


def montar_fato_contrato(e: pd.DataFrame, dims: dict) -> pd.DataFrame:
    f = e.merge(dims["dim_entidade"][["id_entidade", "nif"]], on="nif", how="left")
    f = f.merge(dims["dim_procedimento"], left_on="tipoprocedimento", right_on="tipo", how="left")
    f = f.merge(dims["dim_local"],
                left_on=["local_pais", "local_distrito", "local_concelho"],
                right_on=["pais", "distrito", "concelho"], how="left")
    f = f.merge(dims["dim_cpv"], on="cpv_divisao", how="left")

    preco_base = f["precoBaseProcedimento"].where(f["precoBaseProcedimento"] > 0)   # D12
    preco_efetivo = f["PrecoTotalEfetivo"].where(f["dataFechoContrato"].notna()
                                                 & (f["PrecoTotalEfetivo"] > 0))   # D2

    fato = pd.DataFrame({
        "idcontrato": f["idcontrato"].astype("int64"),
        "id_entidade": f["id_entidade"],
        "id_procedimento": f["id_procedimento"],
        "id_local": f["id_local"],
        "id_cpv": f["id_cpv"],
        "ano_celebracao": f["ano_celebracao"],
        "data_celebracao": texto_data(f["dataCelebracaoContrato"]),
        "data_fecho": texto_data(f["dataFechoContrato"]),
        "tipo_fim": f["tipoFimContrato"],
        "preco_base": preco_base,
        "preco_contratual": f["precoContratual"],
        "preco_efetivo": preco_efetivo,
        "prazo_dias": f["prazoExecucao"],
        "concorrentes": f["concorrentes"],
        "valido_custo": inteiro01(f["valido_custo"]),
        "valido_prazo_fecho": inteiro01(f["valido_prazo_fecho"]),
        "rescindido": inteiro01(f["rescindido"]),
        "cpi_c": f["CPIc"],
        "cpi_c_mod": f["CPIc_mod"],
        "spi_c_fecho": f["SPIc_fecho"],
        "spi_c_formal": f["SPIc_formal"],
        "atraso_dias_fecho": f["atraso_dias_fecho"],
        "prorrogacao_dias": f["prorrogacao_dias"],
        "modificado": inteiro01(f["modificado"]),
        "n_atos": f["n_atos"],
        **{c: inteiro01(f[c]) for c in CAUSAS},
    })
    for col in ["id_entidade", "id_procedimento", "id_local", "id_cpv", "concorrentes", "prazo_dias"]:
        fato[col] = fato[col].astype("Int64")
    return fato


def montar_fato_modificacao(atos: pd.DataFrame) -> pd.DataFrame:
    fato = pd.DataFrame({
        "idcontrato": atos["idcontrato"].astype("int64"),
        "data_modificacao": texto_data(atos["modifContratoData"]),
        "preco_alterado": atos["modifContratoPrecoAlterado"],
        "prazo_alterado": atos["modifPrazoExecucao"].astype("Int64"),
        "fundamentos": atos["fundamentos"],
        **{c: inteiro01(atos[c]) for c in CAUSAS},
    })
    fato.insert(0, "id_ato", range(1, len(fato) + 1))
    return fato


def main() -> None:
    e = pd.read_parquet(PROCESSED / "empreitadas.parquet")
    atos = pd.read_parquet(PROCESSED / "modificacoes_atos.parquet")

    dims = montar_dimensoes(e)
    tabelas = {
        **dims,
        "fato_contrato": montar_fato_contrato(e, dims),
        "fato_modificacao": montar_fato_modificacao(atos),
    }

    if BANCO.exists():
        BANCO.unlink()
    with sqlite3.connect(BANCO) as con:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
        for nome, df in tabelas.items():
            df.to_sql(nome, con, if_exists="append", index=False, chunksize=5000)

        print(f"Banco criado em {BANCO}\n")
        for nome in tabelas:
            n = con.execute(f"SELECT COUNT(*) FROM {nome}").fetchone()[0]
            print(f"  {nome:<18} {n:>9,} linhas")

        orfaos = con.execute("""
            SELECT COUNT(*) FROM fato_contrato
            WHERE id_entidade IS NULL OR id_procedimento IS NULL
        """).fetchone()[0]
        print(f"\n  Contratos sem entidade ou procedimento: {orfaos}")
        problemas = con.execute("PRAGMA foreign_key_check").fetchall()
        print(f"  Chaves estrangeiras quebradas: {len(problemas)}")


if __name__ == "__main__":
    main()
