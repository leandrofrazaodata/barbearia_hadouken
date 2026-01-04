# Setup do Cliente: Barbearia Hadouken

Para finalizar a configuração do novo cliente, você precisa configurar as **Secrets** no repositório do GitHub (Settings > Secrets and variables > Actions).

## 🔑 Secrets Necessárias

| Secret | Descrição | Exemplo |
|--------|-----------|---------|
| `MOTHERDUCK_TOKEN` | Token de acesso ao banco de dados MotherDuck. | `md_...` |
| `OPENAI_API_KEY` | Chave da API da OpenAI para gerar insights. | `sk-...` |
| `EMAIL_USER` | Email Gmail usado para enviar os relatórios. | `seu.email@gmail.com` |
| `EMAIL_PASS` | Senha de App do Gmail (não é a senha normal). | `abcd efgh ijkl mnop` |
| `EMAIL_RECIPIENT` | Email do cliente que receberá o relatório. | `cliente@barbearia.com` |
| `TELEGRAM_TOKEN` | Token do Bot do Telegram para alertas. | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | ID do chat/grupo onde os alertas serão enviados. | `-100123456789` |

## ⚙️ Ajustes no Pipeline

O arquivo `.github/workflows/daily_pipeline.yml` já está configurado, mas verifique se o `TELEGRAM_TOPIC_ID` precisa ser ajustado caso você use tópicos em grupos do Telegram.

## 🚀 Como Rodar

1. Faça o commit e push das alterações.
2. Vá na aba **Actions** do GitHub.
3. Selecione o workflow **Pipeline Diário - Barbearia**.
4. Clique em **Run workflow**.
