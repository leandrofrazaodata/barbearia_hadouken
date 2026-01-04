{{ config(materialized='view') }}

SELECT
    ROW_NUMBER() OVER (ORDER BY strptime(v.data_hora, '%d/%m/%Y %H:%M:%S')) as venda_id,
    REGEXP_REPLACE(CAST(v.telefone AS VARCHAR), '[^0-9]', '', 'g') as cliente_id,
    strptime(v.data_hora, '%d/%m/%Y %H:%M:%S') as data_venda,
    LOWER(TRIM(v.servico)) as servico, 
    COALESCE(p.valor, 0.00) as valor_faturamento
FROM raw_vendas v
LEFT JOIN {{ ref('stg_precos') }} p ON LOWER(TRIM(v.servico)) = p.servico