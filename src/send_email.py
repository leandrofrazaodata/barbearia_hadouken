import duckdb
import yagmail
import os
import json
from datetime import datetime
from openai import OpenAI
from notifications import send_telegram_alert

CONFIG_CLIENTE = {
    "nome_empresa": "Barbearia Hadouken",
    "tipo_negocio": "Barbearia",
    "foco_estrategico": "Fidelização e recorrência.",
    "tom_de_voz": "Profissional e acolhedor."
}

def get_ai_analysis(metricas, top_bairro, historico_recente, top_horario, top_indicador):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "IA indisponível."

    client = OpenAI(api_key=api_key)

    txt_memoria = ""
    if historico_recente:
        txt_memoria = "IMPORTANTE - NÃO REPITA DICAS ANTERIORES:\n" + "\n".join([f"- {h}" for h in historico_recente])

    txt_periodos = "\n".join([f"- {k}: R$ {v['valor']} ({v['qtd']} vendas)" for k, v in metricas['periodos'].items()])

    system_prompt = f"""
    Você é o Consultor Financeiro da 3D Consultoria.
    Cliente: {CONFIG_CLIENTE['nome_empresa']}
    
    DADOS DE HOJE:
    {txt_periodos}
    Ticket Médio: R$ {metricas['ticket_medio']}
    Top Bairro: {top_bairro}
    Melhor Horário: {top_horario}
    Top Indicador: {top_indicador}
    
    {txt_memoria}
    
    TAREFA:
    Dê 1 insight tático NOVO e curto (máx 3 linhas) baseado nos dados.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content
    except:
        return "Sem análise disponível hoje."

def send_report():
    print(">>> [3/3] Gerando Relatório Blindado...")
    token = os.environ.get("MOTHERDUCK_TOKEN")
    con = duckdb.connect(f'md:barbearia_hadouken_db?token={token}')
    
    try:
        # 1. Query Temporal
        query_temporal = """
        SELECT 
            AVG(valor_faturamento) as ticket_medio,
            SUM(CASE WHEN data_venda = CURRENT_DATE - INTERVAL 1 DAY THEN valor_faturamento ELSE 0 END) as valor_ontem,
            COUNT(CASE WHEN data_venda = CURRENT_DATE - INTERVAL 1 DAY THEN 1 END) as qtd_ontem,
            SUM(CASE WHEN date_trunc('week', data_venda) = date_trunc('week', CURRENT_DATE) THEN valor_faturamento ELSE 0 END) as valor_semana,
            COUNT(CASE WHEN date_trunc('week', data_venda) = date_trunc('week', CURRENT_DATE) THEN 1 END) as qtd_semana,
            SUM(CASE WHEN date_trunc('month', data_venda) = date_trunc('month', CURRENT_DATE) THEN valor_faturamento ELSE 0 END) as valor_mes,
            COUNT(CASE WHEN date_trunc('month', data_venda) = date_trunc('month', CURRENT_DATE) THEN 1 END) as qtd_mes
        FROM stg_vendas
        """
        df_tempo = con.execute(query_temporal).df()
        dados = df_tempo.iloc[0]
        
        metricas_ia = {
            "ticket_medio": f"{dados['ticket_medio']:.2f}",
            "periodos": {
                "Ontem": {"valor": f"{dados['valor_ontem']:.2f}", "qtd": int(dados['qtd_ontem'])},
                "Semana Atual": {"valor": f"{dados['valor_semana']:.2f}", "qtd": int(dados['qtd_semana'])},
                "Mês Atual": {"valor": f"{dados['valor_mes']:.2f}", "qtd": int(dados['qtd_mes'])}
            }
        }

        # 2. Dados Auxiliares
        res_bairro = con.execute("SELECT bairro, SUM(total_gasto_ltv) as t FROM mart_dashboard WHERE bairro IS NOT NULL GROUP BY bairro ORDER BY t DESC LIMIT 1").fetchone()
        top_bairro = res_bairro[0] if res_bairro else "Indefinido"
        
        # Novo: Top Horário
        try:
            res_horario = con.execute("SELECT dia_da_semana || ' - ' || periodo_dia, COUNT(*) as c FROM mart_vendas_analitica GROUP BY 1 ORDER BY c DESC LIMIT 1").fetchone()
            top_horario = res_horario[0] if res_horario else "Sem dados"
        except: top_horario = "N/A"

        # Novo: Top Indicador
        try:
            res_indicador = con.execute("SELECT nome_padrinho, total_indicados FROM mart_indicacoes ORDER BY total_indicados DESC LIMIT 1").fetchone()
            top_indicador = f"{res_indicador[0]} ({res_indicador[1]} inds)" if res_indicador else "Nenhum"
        except: top_indicador = "N/A"

        df_vips = con.execute("SELECT nome, total_gasto_ltv, dias_desde_ultima_visita FROM mart_dashboard ORDER BY total_gasto_ltv DESC LIMIT 5").df()

        # 3. Memória
        try:
            historico = con.execute("SELECT insight_gerado FROM historico_ia ORDER BY data_referencia DESC LIMIT 3").fetchall()
            lista_memoria = [h[0] for h in historico]
        except:
            lista_memoria = []

    except Exception as e:
        send_telegram_alert(f"Erro SQL: {e}", level="error")
        raise e

    # 4. Gera Insight e Salva
    insight = get_ai_analysis(metricas_ia, top_bairro, lista_memoria, top_horario, top_indicador)
    try:
        json_metrics = json.dumps(metricas_ia)
        con.execute("INSERT INTO historico_ia (data_referencia, insight_gerado, metricas_json) VALUES (CURRENT_DATE, ?, ?)", [insight, json_metrics])
    except: pass

    # 5. HTML BLINDADO (Table-Based Layout)
    # Convertendo lista VIPs para TRs de tabela
    vip_rows = []
    for _, row in df_vips.iterrows():
        status = "Sumido" if row['dias_desde_ultima_visita'] > 30 else "Ativo"
        vip_rows.append(
            f"<tr><td style='padding:4px;border:1px solid #c9c9c9;'>{row['nome']}</td>"
            f"<td style='padding:4px;border:1px solid #c9c9c9;'>R$ {row['total_gasto_ltv']:.2f}</td>"
            f"<td style='padding:4px;border:1px solid #c9c9c9;text-align:right;'>{status}</td></tr>"
        )
    vip_rows_html = "".join(vip_rows) or "<tr><td colspan='3' style='padding:4px;border:1px solid #c9c9c9;text-align:center;'>Sem dados</td></tr>"

    today_str = datetime.now().strftime('%d/%m/%Y')
    html_body = (
        "<table width='100%' cellpadding='0' cellspacing='0' border='0' "
        "style='border-collapse:collapse;margin:0;padding:0;mso-table-lspace:0pt;mso-table-rspace:0pt;'>"
        "<tr><td align='center' valign='top' style='padding:0;margin:0;'>"
        "<table width='520' cellpadding='0' cellspacing='0' border='0' "
        "style='border-collapse:collapse;margin:0;font-family:Arial,sans-serif;font-size:11px;line-height:1.25;color:#101010;"
        "background:#ffffff;border:1px solid #0b3d91;mso-table-lspace:0pt;mso-table-rspace:0pt;'>"
        f"<tr style='background:#0b3d91;color:#fff;font-weight:bold;text-align:center;'><td colspan='3' style='padding:6px;'>Resumo Gerencial • {today_str}</td></tr>"
        "<tr><td colspan='3' style='padding:6px;border-top:1px solid #d7d7d7;background:#fff2bf;'>"
        "<strong>Consultor 3D:</strong>"
        f"<div style='font-style:italic;margin-top:2px;'>{insight}</div>"
        "</td></tr>"
        "<tr style='background:#0b3d91;color:#fff;font-weight:bold;'>"
        "<th style='padding:4px;border-top:1px solid #0b3d91;border-right:1px solid #ffffff;text-align:left;'>Período</th>"
        "<th style='padding:4px;border-top:1px solid #0b3d91;border-right:1px solid #ffffff;text-align:left;'>Fat. (R$)</th>"
        "<th style='padding:4px;border-top:1px solid #0b3d91;text-align:left;'>Vendas</th>"
        "</tr>"
        f"<tr><td style='padding:4px;border:1px solid #c9c9c9;'>Ontem</td><td style='padding:4px;border:1px solid #c9c9c9;'>{metricas_ia['periodos']['Ontem']['valor']}</td><td style='padding:4px;border:1px solid #c9c9c9;'>{metricas_ia['periodos']['Ontem']['qtd']}</td></tr>"
        f"<tr><td style='padding:4px;border:1px solid #c9c9c9;'>Semana</td><td style='padding:4px;border:1px solid #c9c9c9;color:#0b3d91;font-weight:bold;'>{metricas_ia['periodos']['Semana Atual']['valor']}</td><td style='padding:4px;border:1px solid #c9c9c9;'>{metricas_ia['periodos']['Semana Atual']['qtd']}</td></tr>"
        f"<tr><td style='padding:4px;border:1px solid #c9c9c9;'>Mês</td><td style='padding:4px;border:1px solid #c9c9c9;'>{metricas_ia['periodos']['Mês Atual']['valor']}</td><td style='padding:4px;border:1px solid #c9c9c9;'>{metricas_ia['periodos']['Mês Atual']['qtd']}</td></tr>"
        "<tr style='background:#f2f2f2;font-weight:bold;'><td colspan='3' style='padding:4px;border:1px solid #c9c9c9;'>Indicadores Rápidos</td></tr>"
        f"<tr><td colspan='3' style='padding:4px;border:1px solid #c9c9c9;text-align:center;'>Ticket Médio: <strong>R$ {metricas_ia['ticket_medio']}</strong> • Top Bairro: <strong>{top_bairro}</strong></td></tr>"
        f"<tr><td colspan='3' style='padding:4px;border:1px solid #c9c9c9;text-align:center;'>Pico: <strong>{top_horario}</strong> • Top Indicador: <strong>{top_indicador}</strong></td></tr>"
        "<tr style='background:#f2f2f2;font-weight:bold;'><td colspan='3' style='padding:4px;border:1px solid #c9c9c9;'>Clientes VIPs</td></tr>"
        f"{vip_rows_html}"
        "</table></td></tr></table>"
    )
    
    sender = os.environ.get("EMAIL_USER")
    pwd = os.environ.get("EMAIL_PASS")
    recipient = os.environ.get("EMAIL_RECIPIENT") or "leandro.lf.frazao@hotmail.com"
    
    if sender:
        try:
            print(f"Enviando relatório para: {recipient}")
            yag = yagmail.SMTP(sender, pwd)
            yag.send(
                to=recipient,
                subject=f"Relatório 3D - {datetime.now().strftime('%d/%m')}",
                contents=[yagmail.raw(html_body)]
            )
            print("Relatório enviado!")
        except Exception as e:
            send_telegram_alert(f"Erro envio email: {e}", level="error")
            raise e

if __name__ == "__main__":
    send_report()