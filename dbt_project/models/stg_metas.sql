{{ config(materialized='view') }}

SELECT
    TRY_CAST(mes AS INTEGER) as mes,
    TRY_CAST(ano AS INTEGER) as ano,
    TRY_CAST(meta AS DECIMAL(10,2)) as meta
FROM raw_metas
