"""
Fase 1 - Passo 1: converte as planilhas do IMPIC (xlsx) para parquet.

Lê:   data/raw/contratos<ANO>.xlsx  e  data/raw/modcontra*<ANO>.xlsx
Grava: data/interim/contratos_<ANO>.parquet  e  data/interim/modificacoes_<ANO>.parquet

Rodar uma única vez (ou quando baixar um ano novo), a partir da pasta do projeto:
    python src/converter.py

Os arquivos já convertidos são pulados, então dá para interromper e retomar.
"""

import re
import time
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
INTERIM = RAIZ / "data" / "interim"

# padrão do nome original -> prefixo do arquivo convertido
FONTES = {
    "contratos*.xlsx": "contratos",
    "modcontra*.xlsx": "modificacoes",
}


def ano_do_nome(arquivo: Path) -> str:
    """Extrai o ano (4 dígitos) do nome do arquivo."""
    achado = re.search(r"(20\d{2})", arquivo.stem)
    if not achado:
        raise ValueError(f"Não encontrei o ano no nome: {arquivo.name}")
    return achado.group(1)


def converter(origem: Path, destino: Path) -> None:
    inicio = time.time()
    df = pd.read_excel(origem)

    # Colunas de texto livre com tipos misturados quebram o parquet;
    # convertemos para texto tudo o que não for número nem data.
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype("string")

    df.to_parquet(destino, index=False)
    print(f"  {origem.name} -> {destino.name}: "
          f"{len(df):,} linhas, {time.time() - inicio:.0f} s")


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    for padrao, prefixo in FONTES.items():
        arquivos = sorted(RAW.glob(padrao))
        print(f"\n{prefixo}: {len(arquivos)} arquivos encontrados em {RAW}")
        for origem in arquivos:
            destino = INTERIM / f"{prefixo}_{ano_do_nome(origem)}.parquet"
            if destino.exists():
                print(f"  {destino.name} já existe, pulando")
                continue
            converter(origem, destino)
    print("\nConcluído.")


if __name__ == "__main__":
    main()
