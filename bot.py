import os
import random
from telegram import Bot
from produtos import produtos

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

def montar_mensagem(categoria, itens):
    msg = f"🔥 *OFERTAS DO DIA — {categoria}*\n\n"

    for item in itens:
        msg += f"🛒 *{item['nome']}*\n"
        msg += f"💰 {item['preco']}\n"
        msg += f"🏪 {item['loja']}\n"
        msg += f"👉 {item['link']}\n\n"

    return msg

def escolher_produtos(lista):
    if len(lista) <= 3:
        return lista
    else:
        quantidade = random.randint(3, min(6, len(lista)))
        return random.sample(lista, quantidade)

def executar_bot():
    for categoria, lista_produtos in produtos.items():
        selecionados = escolher_produtos(lista_produtos)

        if not selecionados:
            continue

        mensagem = montar_mensagem(categoria, selecionados)

        bot.send_message(
            chat_id=CHAT_ID,
            text=mensagem,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )

if __name__ == "__main__":
    executar_bot()