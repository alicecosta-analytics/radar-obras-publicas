-- P2: percentagem de empreitadas com estouro de custo (CPIc < 1), por ano.
-- Considera só os contratos com CPIc válido (regras D2 a D4).

SELECT ano_celebracao,
    COUNT(*) AS total_contratos,
    COUNT(cpi_c) AS qtd_CPI_C,
    ROUND (AVG(cpi_c),3) AS media_CPI_C,
    SUM(cpi_c < 1) AS qtd_estouro,
    ROUND ((100.0 * SUM(cpi_c < 1) / COUNT(cpi_c)),1) AS percentual
FROM fato_contrato
WHERE ano_celebracao BETWEEN 2018 AND 2023
GROUP BY ano_celebracao
ORDER BY ano_celebracao;
