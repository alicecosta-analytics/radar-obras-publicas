-- P3: percentagem de empreitadas com estouro de custo (CPIc < 1), por tipo de procedimento, 2019-2022.
-- Só procedimentos com pelo menos 100 contratos com CPIc válido (grupos menores não dão percentagens confiáveis).

SELECT d.tipo,
    COUNT(*) AS total_contratos,
    COUNT(cpi_c) AS qtd_cpi_c,
    ROUND ((100.0 * SUM(cpi_c < 1) / COUNT(cpi_c)),1) AS percentual
FROM fato_contrato AS f
JOIN dim_procedimento AS d
    ON f.id_procedimento = d.id_procedimento
WHERE f.ano_celebracao BETWEEN 2019 AND 2022
GROUP BY d.tipo
HAVING COUNT(cpi_c) >= 100
ORDER BY total_contratos DESC


