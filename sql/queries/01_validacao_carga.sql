-- P1 / gate da Fase 1, refeito em SQL:
-- empreitadas, encerramento reportado e contratos válidos por ano de celebração.
-- Deve reproduzir o log_exclusoes.csv do transform.py.

SELECT
    ano_celebracao,
    COUNT(*)                                        AS empreitadas,
    ROUND(100.0 * AVG(data_fecho IS NOT NULL), 1)   AS com_fecho_pct,
    SUM(valido_custo)                               AS validos_custo,
    SUM(modificado)                                 AS modificados,
    ROUND(SUM(preco_contratual) / 1e6, 1)           AS valor_contratado_meur
FROM fato_contrato
GROUP BY ano_celebracao
ORDER BY ano_celebracao;
