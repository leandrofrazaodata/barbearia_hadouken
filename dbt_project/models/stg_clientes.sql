{{ config(materialized='view') }}

SELECT
    -- Usando telefone limpo como ID
    REGEXP_REPLACE(CAST(telefone AS VARCHAR), '[^0-9]', '', 'g') as cliente_id,
    UPPER(TRIM(nome)) as nome,
    try_strptime(data_nascimento, '%d/%m/%Y')::DATE as data_nascimento,
    UPPER(TRIM(bairro)) as bairro,
    UPPER(TRIM(indicacao)) as indicacao,
    REGEXP_REPLACE(CAST(tel_indicacao AS VARCHAR), '[^0-9]', '', 'g') as tel_indicacao
-- MUDANÇA AQUI: Lendo direto da tabela raw carregada pelo Python
FROM raw_clientes