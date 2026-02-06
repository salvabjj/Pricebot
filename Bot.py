import os
import json
import requests
from bs4 import BeautifulSoup
from telegram import Bot, ParseMode

# Variáveis do GitHub Secrets
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def main():
    if not TOKEN or not CHAT_ID:
        print("ERRO: Configure as Secrets no GitHub!")
        return

    bot = Bot(token=TOKEN)
    
    # Busca a oferta (exemplo simplificado)
    url = "https://www.mercadolivre.com.br/ofertas"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Pega o primeiro item da lista de ofertas
        item = soup.find("p", class_="promotion-item__title")
        preco = soup.find("span", class_="andes-money-amount__fraction")
        link = soup.find("a", class_="promotion-item__link-container")

        if item and preco:
            msg = f"🔥 *OFERTA:* {item.text}\n💰 *PREÇO:* R$ {preco.text}\n🛒 [COMPRAR]({link['href']})"
            bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
            print("✅ Postado!")
        else:
            print("0 ofertas encontradas.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
