-- D11: medianas dos índices de custo e de prazo, por ano (2018-2023).
-- O SQLite não tem uma função MEDIAN pronta; a mediana é calculada
-- ordenando os valores de cada ano e pegando o do meio.
--
-- Conceitos-chave:
--   WITH (CTE): dá nome a uma etapa intermediária e permite usá-la depois,
--   como uma tabela temporária. Resolve o problema de não poder usar um
--   apelido no mesmo SELECT.
--   Funções de janela (OVER): calculam algo sobre um grupo de linhas SEM
--   juntar as linhas num monte, como faz o GROUP BY.
--     ROW_NUMBER() OVER (PARTITION BY ano ORDER BY valor) -> posição de cada
--       contrato dentro do seu ano, do menor para o maior valor.
--     COUNT(*) OVER (PARTITION BY ano) -> quantos contratos tem o ano,
--       repetido em cada linha.
--   O meio: com n ímpar, a posição (n+1)/2; com n par, a média das posições
--   n/2 e n/2+1. As expressões (n+1)/2 e (n+2)/2 usam a divisão inteira de
--   propósito: dão a mesma posição se n for ímpar e as duas do meio se n for par.

WITH custo AS (
    SELECT ano_celebracao,
           cpi_c                                                                  AS valor,
           ROW_NUMBER() OVER (PARTITION BY ano_celebracao ORDER BY cpi_c)         AS pos,
           COUNT(*)     OVER (PARTITION BY ano_celebracao)                        AS n
    FROM fato_contrato
    WHERE cpi_c IS NOT NULL
      AND ano_celebracao BETWEEN 2018 AND 2023
),
prazo AS (
    SELECT ano_celebracao,
           spi_c_fecho                                                            AS valor,
           ROW_NUMBER() OVER (PARTITION BY ano_celebracao ORDER BY spi_c_fecho)   AS pos,
           COUNT(*)     OVER (PARTITION BY ano_celebracao)                        AS n
    FROM fato_contrato
    WHERE spi_c_fecho IS NOT NULL
      AND ano_celebracao BETWEEN 2018 AND 2023
),
mediana_custo AS (
    SELECT ano_celebracao, n AS n_custo, AVG(valor) AS mediana_cpi_c
    FROM custo
    WHERE pos IN ((n + 1) / 2, (n + 2) / 2)
    GROUP BY ano_celebracao, n
),
mediana_prazo AS (
    SELECT ano_celebracao, n AS n_prazo, AVG(valor) AS mediana_spi_c_fecho
    FROM prazo
    WHERE pos IN ((n + 1) / 2, (n + 2) / 2)
    GROUP BY ano_celebracao, n
)
SELECT c.ano_celebracao,
       c.n_custo,
       ROUND(c.mediana_cpi_c, 3)          AS mediana_cpi_c,
       p.n_prazo,
       ROUND(p.mediana_spi_c_fecho, 3)    AS mediana_spi_c_fecho
FROM mediana_custo AS c
JOIN mediana_prazo AS p
    ON c.ano_celebracao = p.ano_celebracao
ORDER BY c.ano_celebracao;
