import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from dotenv import load_dotenv
from database import DatabaseManager
import asyncio
from telegram.error import TimedOut, NetworkError, RetryAfter

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
db_manager = DatabaseManager()

# Configurações de timeout e retry
CONNECT_TIMEOUT = 30.0  # segundos
READ_TIMEOUT = 30.0    # segundos
RETRY_ATTEMPTS = 3     # número de tentativas
RETRY_DELAY = 5       # segundos entre tentativas

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "Olá! Sou um bot que pode responder suas perguntas. Como posso ajudar?"
        )
    except (TimedOut, NetworkError) as e:
        print(f"Erro ao enviar mensagem de start: {e}")
        await asyncio.sleep(RETRY_DELAY)
        await update.message.reply_text(
            "Olá! Sou um bot que pode responder suas perguntas. Como posso ajudar?"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Salva a mensagem no histórico
    db_manager.salvar_mensagem_historico(user_id, user_message)
    
    # Busca o histórico de mensagens do usuário
    historico = db_manager.buscar_historico_usuario(user_id)
    
    # Monta o contexto da conversa com o histórico
    contexto_conversa = "Histórico da conversa:\n"
    for msg in reversed(historico[1:]):  # Exclui a mensagem atual
        contexto_conversa += f"Usuário: {msg}\n"
    contexto_conversa += f"\nPergunta atual: {user_message}"
    
    # Tenta buscar resposta no banco de dados com o contexto
    for attempt in range(RETRY_ATTEMPTS):
        try:
            resposta_db = db_manager.buscar_resposta(contexto_conversa)
            if resposta_db:
                await update.message.reply_text(resposta_db)
                return
            break
        except (TimedOut, NetworkError) as e:
            print(f"Tentativa {attempt + 1} falhou: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_DELAY)
            continue
        except RetryAfter as e:
            print(f"Rate limit atingido, aguardando {e.retry_after} segundos")
            await asyncio.sleep(e.retry_after)
            continue
        except Exception as e:
            print(f"Erro inesperado: {e}")
            break
    
    try:
        await update.message.reply_text("Desculpe, não encontrei informações para responder sua pergunta.")
    except (TimedOut, NetworkError):
        print("Não foi possível enviar mensagem de erro")

def main():
    # Inicializa o bot com configurações de timeout
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(CONNECT_TIMEOUT)
        .read_timeout(READ_TIMEOUT)
        .get_updates_read_timeout(READ_TIMEOUT)
        .build()
    )
    
    # Adiciona os handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Inicia o bot
    print("Bot iniciado...")
    while True:
        try:
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        except (TimedOut, NetworkError) as e:
            print(f"Erro de conexão: {e}")
            print(f"Tentando reconectar em {RETRY_DELAY} segundos...")
            asyncio.sleep(RETRY_DELAY)
            continue
        except Exception as e:
            print(f"Erro fatal: {e}")
            break
        finally:
            db_manager.fechar_conexao()

if __name__ == "__main__":
    main() 