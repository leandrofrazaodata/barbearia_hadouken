{{ config(materialized='view') }}

SELECT
    LOWER(TRIM(servico)) as servico,
    try_strptime(data_criacao, '%d/%m/%Y')::DATE as data_criacao,
    TRY_CAST(REPLACE(valor, ',', '.') AS DECIMAL(10,2)) as valor
FROM raw_precos