# Bot de Consultas SQL via Telegram

Este é um bot do Telegram que permite fazer consultas em um banco de dados MySQL através de linguagem natural, utilizando a API Deepseek para converter as perguntas em consultas SQL. Utilizei a IA do Deepseek pelos tokens serem bem baratos em relação a outras IA's. 

## 🚀 Funcionalidades

- Processamento de linguagem natural para consultas SQL
- Histórico de conversas (mantém as últimas 5 mensagens do usuário)
- Sistema de retry para lidar com problemas de conexão
- Tratamento de timeouts e erros de rede
- Formatação automática das respostas

## 📋 Pré-requisitos

- Python 3.8+
- MySQL Server
- Token do Bot Telegram
- Chave de API Deepseek

## 🔧 Observações de uso

1. Instale as dependências via shell na sua IDE:
- pip install -r requirements.txt
  
2. Configure o banco de dados:
- Crie um banco de dados MySQL
- Configure os dados de conexão do seu banco de dados no arquivo `.env`

3. Na função buscar_resposta do arquivo database.py, configure como a IA deve se comportar diante dos seus dados.

## 🎮 Uso

1. Inicie o bot (arquivo bot.py)
2. Após rodar, vá ao Telegram e inicie uma conversa com o bot usando o comando `/start`
3. Faça perguntas sobre os dados do seu banco de dados em linguagem natural
### Exemplos de perguntas:
- "Quais são os dados da tabela X?"
- "Mostre todas as informações sobre Y"
- "Quantos registros existem na tabela Z?"

## 🛠️ Estrutura do Projeto

- `bot.py`: Arquivo principal com a lógica do bot Telegram
- `database.py`: Gerenciamento de conexão e consultas ao banco de dados
- `.env`: Arquivo de configuração com variáveis de ambiente
- `requirements.txt`: Lista de dependências do projeto

## ⚙️ Configurações

### Timeouts e Retries
- Timeout de conexão: 30 segundos
- Timeout de leitura: 30 segundos
- Tentativas de retry: 3
- Delay entre retries: 5 segundos

### Histórico de Mensagens
- Armazena as últimas 5 mensagens por usuário
- Mensagens mais antigas são automaticamente removidas

## 📦 Dependências Principais

- python-telegram-bot
- mysql-connector-python
- python-dotenv
- requests

## ✒️ Dev

* **João Pedro Araujo** - *Engenheiro de Software Jr.* - [jparr2407](https://github.com/jparr2407)
