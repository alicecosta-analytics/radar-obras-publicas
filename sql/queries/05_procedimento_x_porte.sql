-- P3 x P4: o concurso público estoura mais por causa do procedimento ou do porte?
-- Compara os três procedimentos principais DENTRO da mesma faixa de porte.
-- Se o concurso continuar estourando mais em todas as faixas, o porte
-- sozinho não explica a diferença vista na consulta 03.
-- Empreitadas de 2019-2022; só combinações com pelo menos 100 contratos com CPIc.
--
-- Conceitos-chave:
--   GROUP BY com duas colunas: cada linha é uma combinação procedimento x faixa.
--   IN: testa se o valor está numa lista (equivale a vários OR).

SELECT
    CASE
        WHEN f.preco_contratual <= 150000    THEN '1. até 150 mil'
        WHEN f.preco_contratual <= 1000000   THEN '2. 150 mil a 1 milhão'
        WHEN f.preco_contratual <= 5000000   THEN '3. 1 a 5 milhões'
        ELSE                                      '4. acima de 5 milhões'
    END                                                         AS faixa_porte,
    d.tipo                                                      AS procedimento,
    COUNT(*)                                                    AS total_contratos,
    COUNT(f.cpi_c)                                              AS qtd_cpi_c,
    ROUND(100.0 * SUM(f.cpi_c < 1) / COUNT(f.cpi_c), 1)         AS pct_estouro_custo
FROM fato_contrato AS f
JOIN dim_procedimento AS d
    ON f.id_procedimento = d.id_procedimento
WHERE f.ano_celebracao BETWEEN 2019 AND 2022
  AND f.preco_contratual IS NOT NULL
  AND d.tipo IN ('Concurso público', 'Consulta Prévia', 'Ajuste Direto Regime Geral')
GROUP BY faixa_porte, d.tipo
HAVING COUNT(f.cpi_c) >= 100
ORDER BY faixa_porte, d.tipo;
