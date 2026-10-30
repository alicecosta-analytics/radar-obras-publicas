-- P4: o porte da obra está ligado ao estouro de custo?
-- Empreitadas de 2019-2022, em quatro faixas de preço contratual.
-- Considera só os contratos com CPIc válido para a percentagem (regras D2 a D4).
--
-- Conceito-chave: CASE WHEN testa as condições de cima para baixo e para na
-- primeira verdadeira. Por isso cada linha só precisa do limite superior.
-- Os números na frente dos nomes ("1.", "2."...) fazem a ordenação respeitar
-- a ordem das faixas, e não a ordem alfabética.

SELECT
    CASE
        WHEN preco_contratual IS NULL      THEN '0. sem preço'
        WHEN preco_contratual <= 150000    THEN '1. até 150 mil'
        WHEN preco_contratual <= 1000000   THEN '2. 150 mil a 1 milhão'
        WHEN preco_contratual <= 5000000   THEN '3. 1 a 5 milhões'
        ELSE                                    '4. acima de 5 milhões'
    END                                                     AS faixa_porte,
    COUNT(*)                                                AS total_contratos,
    COUNT(cpi_c)                                            AS qtd_cpi_c,
    ROUND(100.0 * SUM(cpi_c < 1) / COUNT(cpi_c), 1)         AS pct_estouro_custo,
    ROUND(AVG(cpi_c), 3)                                    AS media_cpi_c
FROM fato_contrato
WHERE ano_celebracao BETWEEN 2019 AND 2022
GROUP BY faixa_porte
ORDER BY faixa_porte;
