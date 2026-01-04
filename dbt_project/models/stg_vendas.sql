{{ config(materialized='view') }}

SELECT
    ROW_NUMBER() OVER (ORDER BY v.data_hora) as venda_id,
    REGEXP_REPLACE(v.telefone, '[^0-9]', '', 'g') as cliente_id,
    v.data_hora::TIMESTAMP as data_venda,
    LOWER(TRIM(v.servico)) as servico, 
    COALESCE(p.valor, 0.00) as valor_faturamento
FROM raw_vendas v
LEFT JOIN {{ ref('stg_precos') }} p ON LOWER(TRIM(v.servico)) = p.servico