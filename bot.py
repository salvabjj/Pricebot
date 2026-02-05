import os
import json
import requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# =====================
# CONFIGURAÇÕES
# =====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HISTORY_FILE = "history.json"

LINKS = [
    # Eletrodomésticos
    {"categoria": "Eletrodomésticos", "url": "https://amzn.to/46iUEb6"},
    {"categoria": "Eletrodomésticos", "url": "https://amzn.to/3NR54IP"},

    # Moda / Calçados
    {"categoria": "Moda Masculina", "url": "https://www.netshoes.com.br/p/tenis-couro-adidas-grand-court-alpha-masculino-marrom-FB9-8951-138"},

    # Marketplaces
    {"categoria": "Moda Feminina", "url": "https://mercadolivre.com/sec/33LveAZ"},
    {"categoria": "Moda Feminina", "url": "https://mercadolivre.com/sec/26Rjo9j"},

    # Esportes
    {"categoria": "Esportes - Basquete", "url": "https://s.shopee.com.br/8KjpTzVMDC"},
    {"categoria": "Esportes - Futebol", "url": "https://s.shopee.com.br/BO7l1QAut"},
]

# =====================
# HISTÓRICO (SEGURO)
# =====================
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except:
        return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# =====================
# SCRAPER BÁSICO
# =====================
def get_product_info(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)

    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.title.text.strip() if soup.title else "Oferta imperdível"

    image = None
    img_tag = soup.find("img")
    if img_tag and img_tag.get("src"):
        image = img_tag["src"]

    return {
        "title": title,
        "image": image,
        "link": url
    }

# =====================
# ENVIO TELEGRAM
# =====================
def send_product(bot, produto):
    text = f"🔥 *{produto['categoria']}*\n\n{produto['title']}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Ver oferta", url=produto["link"])]
    ])

    if produto["image"] and produto["image"].startswith("http"):
        try:
            bot.send_photo(
                chat_id=CHAT_ID,
                photo=produto["image"],
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        except:
            pass

    bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# =====================
# MAIN
# =====================
def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    history = load_history()
    enviado = False

    for item in LINKS:
        if item["url"] in history:
            continue

        produto = get_product_info(item["url"])
        produto["categoria"] = item["categoria"]

        send_product(bot, produto)

        history.append(item["url"])
        save_history(history)

        enviado = True
        break

    if not enviado:
        bot.send_message(
            chat_id=CHAT_ID,
            text="⚠️ Nenhuma nova oferta encontrada nesta execução."
        )

if __name__ == "__main__":
    main()