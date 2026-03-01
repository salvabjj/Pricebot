import os
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_POST = os.getenv("CHAT_ID_POST")
CHAT_REPORT = os.getenv("CHAT_ID_REPORT")

bot = Bot(token=TOKEN)

def enviar_oferta(texto):
    bot.send_message(chat_id=CHAT_POST, text=texto)

def enviar_relatorio(texto):
    bot.send_message(chat_id=CHAT_REPORT, text=texto)
