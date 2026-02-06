import requests
from bs4 import BeautifulSoup
from telegram import Bot, ParseMode
import time

# Configurações do Telegram
TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"

# Headers para simular um navegador real e evitar bloqueios
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
}

def buscar_oferta():
    url = "https://www.mercadolivre.com.br/ofertas"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"Erro no site: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Seletores resilientes (buscam por classes comuns de oferta)
        produto = soup.find("p", class_="promotion-item__title")
        preco = soup.find("span", class_="andes-money-amount__fraction")
        link = soup.find("a", class_="promotion-item__link-container")

        if produto and preco:
            return {
                "titulo": produto.text.strip(),
                "valor": preco.text.strip(),
                "url": link['href'] if link else url
            }
    except Exception as e:
        print(f"Erro no scraping: {e}")
    return None

def main():
    bot = Bot(token=TOKEN)
    print("🤖 Iniciando monitoramento...")
    
    oferta = buscar_oferta()
    
    if oferta:
        msg = (
            f"🔥 *OFERTA ENCONTRADA*\n\n"
            f"📦 {oferta['titulo']}\n"
            f"💰 *R$ {oferta['valor']}*\n\n"
            f"🛒 [VER NO SITE]({oferta['url']})"
        )
        # Na v13.15, o envio é síncrono (sem await)
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
        print("✅ Mensagem enviada!")
    else:
        print("0 ofertas capturadas nesta rodada.")

if __name__ == "__main__":
    main()
