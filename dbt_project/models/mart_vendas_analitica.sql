{{ config(materialized='table') }}

WITH vendas AS (
    SELECT * FROM {{ ref('stg_vendas') }}
),
clientes AS (
    SELECT * FROM {{ ref('stg_clientes') }}
)

SELECT
    v.venda_id,
    v.data_venda,
    -- Extraindo inteligência temporal
    CASE strftime(v.data_venda, '%w')
        WHEN '0' THEN 'Domingo'
        WHEN '1' THEN 'Segunda'
        WHEN '2' THEN 'Terça'
        WHEN '3' THEN 'Quarta'
        WHEN '4' THEN 'Quinta'
        WHEN '5' THEN 'Sexta'
        WHEN '6' THEN 'Sábado'
    END as dia_da_semana,
    EXTRACT(HOUR FROM v.data_venda) as hora_do_dia,
    CASE 
        WHEN EXTRACT(HOUR FROM v.data_venda) < 12 THEN 'Manhã'
        WHEN EXTRACT(HOUR FROM v.data_venda) < 18 THEN 'Tarde'
        ELSE 'Noite'
    END as periodo_dia,
    
    v.servico,
    v.valor_faturamento,
    
    -- Dados do Cliente
    c.nome as nome_cliente,
    c.bairro as bairro_cliente,
    c.indicacao as veio_por_indicacao
    
FROM vendas v
LEFT JOIN clientes c ON v.cliente_id = c.cliente_id
