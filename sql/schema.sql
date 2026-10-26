-- =====================================================================
-- Radar de Desvios de Prazo e Custo em Obras Públicas
-- Modelo dimensional (esquema em estrela) - SQLite
--
-- Duas tabelas fato (contratos e atos de modificação) e quatro dimensões.
-- Gerado e carregado por src/load.py a partir de data/processed/.
-- Convenções: datas em texto ISO (AAAA-MM-DD); verdadeiro/falso em 0/1.
-- =====================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fato_modificacao;
DROP TABLE IF EXISTS fato_contrato;
DROP TABLE IF EXISTS dim_entidade;
DROP TABLE IF EXISTS dim_procedimento;
DROP TABLE IF EXISTS dim_local;
DROP TABLE IF EXISTS dim_cpv;

-- ---------------------------------------------------------------- dimensões

-- Entidade adjudicante (dono da obra). Chave natural: NIF.
CREATE TABLE dim_entidade (
    id_entidade   INTEGER PRIMARY KEY,
    nif           TEXT,
    nome          TEXT NOT NULL
);

-- Tipo de procedimento de contratação (concurso público, ajuste direto...)
CREATE TABLE dim_procedimento (
    id_procedimento  INTEGER PRIMARY KEY,
    tipo             TEXT NOT NULL UNIQUE
);

-- Local de execução (primeiro local declarado no contrato)
CREATE TABLE dim_local (
    id_local   INTEGER PRIMARY KEY,
    pais       TEXT,
    distrito   TEXT,
    concelho   TEXT
);

-- Tipo de obra pelo código CPV (3 primeiros dígitos)
CREATE TABLE dim_cpv (
    id_cpv        INTEGER PRIMARY KEY,
    cpv_divisao   TEXT NOT NULL UNIQUE
);

-- ---------------------------------------------------------------- fatos

-- Uma linha por empreitada de obras públicas (decisão D1)
CREATE TABLE fato_contrato (
    idcontrato            INTEGER PRIMARY KEY,
    id_entidade           INTEGER REFERENCES dim_entidade(id_entidade),
    id_procedimento       INTEGER REFERENCES dim_procedimento(id_procedimento),
    id_local              INTEGER REFERENCES dim_local(id_local),
    id_cpv                INTEGER REFERENCES dim_cpv(id_cpv),

    ano_celebracao        INTEGER NOT NULL,
    data_celebracao       TEXT,
    data_fecho            TEXT,
    tipo_fim              TEXT,

    -- Linha de base e execução
    preco_base            REAL,      -- zero tratado como ausente (D12)
    preco_contratual      REAL,
    preco_efetivo         REAL,      -- só válido com fecho (D2)
    prazo_dias            INTEGER,
    concorrentes          INTEGER,

    -- Flags de validade (D2 a D5)
    valido_custo          INTEGER NOT NULL,
    valido_prazo_fecho    INTEGER NOT NULL,
    rescindido            INTEGER NOT NULL,

    -- Índices (vazios onde o contrato não passa nas regras)
    cpi_c                 REAL,      -- custo, medida direta
    cpi_c_mod             REAL,      -- custo, limite inferior (D8)
    spi_c_fecho           REAL,      -- prazo, limite superior (D5)
    spi_c_formal          REAL,      -- prazo, limite inferior (D7)
    atraso_dias_fecho     REAL,
    prorrogacao_dias      REAL,

    -- Resumo das modificações
    modificado                  INTEGER NOT NULL,
    n_atos                      INTEGER NOT NULL,
    causa_trab_complementares   INTEGER NOT NULL,
    causa_trab_a_menos          INTEGER NOT NULL,
    causa_revisao_ordinaria     INTEGER NOT NULL,
    causa_crise_precos          INTEGER NOT NULL,
    causa_interesse_publico     INTEGER NOT NULL,
    causa_prorrogacao           INTEGER NOT NULL
);

-- Uma linha por ato de modificação (D9: fundamentos do mesmo ato agrupados)
CREATE TABLE fato_modificacao (
    id_ato                      INTEGER PRIMARY KEY,
    idcontrato                  INTEGER NOT NULL,   -- pode não estar em fato_contrato (outros tipos de contrato)
    data_modificacao            TEXT,
    preco_alterado              REAL,               -- novo preço total, não o acréscimo
    prazo_alterado              INTEGER,            -- novo prazo total, em dias
    fundamentos                 TEXT,
    causa_trab_complementares   INTEGER NOT NULL,
    causa_trab_a_menos          INTEGER NOT NULL,
    causa_revisao_ordinaria     INTEGER NOT NULL,
    causa_crise_precos          INTEGER NOT NULL,
    causa_interesse_publico     INTEGER NOT NULL,
    causa_prorrogacao           INTEGER NOT NULL
);

-- ---------------------------------------------------------------- índices

CREATE INDEX ix_contrato_ano        ON fato_contrato(ano_celebracao);
CREATE INDEX ix_contrato_entidade   ON fato_contrato(id_entidade);
CREATE INDEX ix_contrato_proc       ON fato_contrato(id_procedimento);
CREATE INDEX ix_modificacao_contr   ON fato_modificacao(idcontrato);
