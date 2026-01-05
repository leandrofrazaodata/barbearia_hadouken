import pandas as pd
import duckdb
import os
from notifications import send_telegram_alert

# --- CONFIGURAÇÃO ---
# O ID GERAL DA PLANILHA
SHEET_ID = "1mI5xa3AZSjSqzT1jDijsiMWAtnY-f1a_fLC0Je1Otkw"

# Aba Clientes
# Substitua o GID pelo valor correto da aba 'cliente'
GID_CLIENTES = "705989490" 
URL_CLIENTES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_CLIENTES}"

# Aba Vendas
# Substitua o GID pelo valor correto da aba 'venda'
GID_VENDAS = "517304213" 
URL_VENDAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_VENDAS}"

# Aba Preços (Necessária para calcular faturamento)
# Substitua o GID pelo valor correto da aba 'precos'
GID_PRECOS = "1977854161"
URL_PRECOS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_PRECOS}"

# Aba Metas
GID_METAS = "1524491873"
URL_METAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_METAS}"

def run_pipeline():
    print(">>> [1/4] Iniciando Ingestão e Infraestrutura...")
    
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        raise Exception("MOTHERDUCK_TOKEN não configurado!")

    con = duckdb.connect(f'md:?token={token}')
    
    # 1. Garante o Banco
    con.execute("CREATE DATABASE IF NOT EXISTS barbearia_hadouken_db")
    con.execute("USE barbearia_hadouken_db")

    # 2. Garante a Tabela de MEMÓRIA DA IA (Novidade!)
    print("Verificando tabela de histórico da IA...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS historico_ia (
            data_referencia DATE,
            insight_gerado VARCHAR,
            metricas_json VARCHAR,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Carrega Dados (Load)
    files = {
        "raw_clientes": URL_CLIENTES,
        "raw_vendas": URL_VENDAS,
        "raw_precos": URL_PRECOS,
        "raw_metas": URL_METAS
    }

    for table_name, url in files.items():
        try:
            print(f"Processando {table_name}...")
            # Force all columns to be strings to avoid type inference issues (e.g. phone numbers as floats)
            df = pd.read_csv(url, on_bad_lines='warn', dtype=str)
            
            if len(df.columns) > 0 and "<!DOCTYPE" in str(df.columns[0]):
                raise Exception("ERRO: Link baixou HTML. Verifique o GID.")

            if len(df) == 0:
                send_telegram_alert(f"⚠️ {table_name} vazio!", level="warning")

            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            print(f"✅ {table_name}: {len(df)} linhas.")
            
        except Exception as e:
            send_telegram_alert(f"Erro no {table_name}: {e}", level="error")
            raise e

if __name__ == "__main__":
    run_pipeline()