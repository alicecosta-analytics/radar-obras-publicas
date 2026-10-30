-- P5: custo e prazo estouram juntos?
-- Entre as empreitadas de 2019-2022 com CPIc válido, compara quem estourou o
-- custo com quem não estourou, olhando o prazo pelas duas medidas do desenho
-- em intervalo (D7): a prorrogação formal (limite inferior) e o tempo até o
-- fecho (limite superior).
--
-- Conceitos-chave:
--   CASE WHEN dentro do GROUP BY para criar os dois grupos.
--   COALESCE(x, 0): troca NULL por 0. Contratos sem modificação não têm
--   prorrogação registada, o que aqui significa "zero dias prorrogados".
-- A correlação de Spearman entre os dois índices fica para a Fase 3, em Python.

SELECT
    CASE WHEN cpi_c < 1 THEN 'estourou o custo' ELSE 'não estourou o custo' END   AS grupo_custo,
    COUNT(*)                                                                       AS contratos,
    ROUND(100.0 * AVG(COALESCE(prorrogacao_dias, 0) > 0), 1)                       AS pct_com_prorrogacao_formal,
    ROUND(AVG(COALESCE(prorrogacao_dias, 0)), 0)                                   AS prorrogacao_media_dias,
    ROUND(AVG(atraso_dias_fecho), 0)                                               AS atraso_medio_ate_fecho_dias,
    ROUND(100.0 * AVG(spi_c_fecho < 1), 1)                                         AS pct_fecho_apos_prazo
FROM fato_contrato
WHERE ano_celebracao BETWEEN 2019 AND 2022
  AND cpi_c IS NOT NULL
GROUP BY grupo_custo
ORDER BY grupo_custo;
