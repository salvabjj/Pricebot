import os
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_POST = os.getenv("-1003858741896")
CHAT_REPORT = os.getenv("8309912019")

bot = Bot(token=8056783817:AAHPYbLVK8tt7uYnVIjPg77J3VIVya_YF18)

def enviar_oferta(texto):
    bot.send_message(chat_id=CHAT_POST, text=texto)

def enviar_relatorio(texto):
    bot.send_message(chat_id=CHAT_REPORT, text=texto)
