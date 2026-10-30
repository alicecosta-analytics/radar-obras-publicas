-- P7: por que os contratos foram modificados, e a crise de preços de 2021-2022 aparece?
-- Por ano de celebração (2018-2022, os anos com base de modificações),
-- a parcela de empreitadas modificadas e, entre elas, a parcela com cada causa.
-- Um contrato pode ter várias causas, então as percentagens não somam 100.
--
-- As colunas causa_* da fato_contrato valem 1 se QUALQUER ato do contrato
-- teve aquela causa (resumo feito no transform.py). Usar a fato_contrato,
-- e não a fato_modificacao, evita contar o mesmo contrato várias vezes.
--
-- Conceito-chave: AVG de uma coluna 0/1 é a proporção de 1s.
-- Filtrar só os modificados dentro da conta: SUM(condição) / SUM(modificado).

SELECT
    ano_celebracao,
    COUNT(*)                                                                  AS empreitadas,
    SUM(modificado)                                                           AS modificadas,
    ROUND(100.0 * AVG(modificado), 1)                                         AS pct_modificadas,
    ROUND(100.0 * SUM(causa_trab_complementares) / SUM(modificado), 1)        AS pct_trab_complementares,
    ROUND(100.0 * SUM(causa_trab_a_menos)        / SUM(modificado), 1)        AS pct_trab_a_menos,
    ROUND(100.0 * SUM(causa_revisao_ordinaria)   / SUM(modificado), 1)        AS pct_revisao_ordinaria,
    ROUND(100.0 * SUM(causa_crise_precos)        / SUM(modificado), 1)        AS pct_crise_precos,
    ROUND(100.0 * SUM(causa_interesse_publico)   / SUM(modificado), 1)        AS pct_interesse_publico,
    ROUND(100.0 * SUM(causa_prorrogacao)         / SUM(modificado), 1)        AS pct_prorrogacao
FROM fato_contrato
WHERE ano_celebracao BETWEEN 2018 AND 2022
GROUP BY ano_celebracao
ORDER BY ano_celebracao;
