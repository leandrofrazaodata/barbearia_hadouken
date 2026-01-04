{{ config(materialized='table') }}

WITH clientes AS (
    SELECT * FROM {{ ref('stg_clientes') }}
),
metricas_clientes AS (
    SELECT * FROM {{ ref('mart_dashboard') }}
)

SELECT
    -- Quem indicou (Padrinho)
    c.tel_indicacao as telefone_padrinho,
    padrinho.nome as nome_padrinho,
    
    -- Métricas do Padrinho
    COUNT(c.cliente_id) as total_indicados,
    SUM(mc.total_gasto_ltv) as valor_gerado_pelos_indicados
    
FROM clientes c
-- Auto-join para achar o nome de quem indicou
LEFT JOIN clientes padrinho ON c.tel_indicacao = padrinho.cliente_id
LEFT JOIN metricas_clientes mc ON c.cliente_id = mc.cliente_id
WHERE c.tel_indicacao IS NOT NULL AND c.tel_indicacao != ''
GROUP BY 1, 2
ORDER BY total_indicados DESC
