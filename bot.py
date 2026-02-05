import os
import json
import random
import requests
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

POSTS_PER_RUN = 3

# =========================
# AFILIADOS
# =========================
AMAZON_TAG = "salvablessjj-20"

# =========================
# TELEGRAM
# =========================
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()

# =========================
# AMAZON SCRAPER (SIMPLES)
# =========================
def scrape_amazon(query):
    url = f"https://www.amazon.com.br/s?k={query}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    products = []

    for item in soup.select("div[data-component-type='s-search-result']"):
        title = item.select_one("h2 span")
        link = item.select_one("h2 a")
        price = item.select_one("span.a-offscreen")

        if not title or not link:
            continue

        name = title.text.strip()
        href = link["href"]

        if "dp/" not in href:
            continue

        price_value = "Consulte o preço"
        if price:
            price_value = price.text.strip()

        full_link = f"https://www.amazon.com.br{href}"
        if "tag=" not in full_link:
            sep = "&" if "?" in full_link else "?"
            full_link += f"{sep}tag={AMAZON_TAG}"

        products.append({
            "name": name,
            "price": price_value,
            "url": full_link
        })

    return products

# =========================
# MAIN
# =========================
def main():
    queries = [
        "tenis esportivo",
        "moda masculina",
        "moda feminina",
        "moda infantil",
        "suplementos"
    ]

    all_products = []

    for q in queries:
        try:
            all_products.extend(scrape_amazon(q))
        except Exception as e:
            print("Erro Amazon:", e)

    if not all_products:
        send_message("⚠️ Nenhuma oferta encontrada nesta execução.")
        return

    random.shuffle(all_products)
    selected = all_products[:POSTS_PER_RUN]

    for p in selected:
        msg = (
            f"🔥 OFERTA EM DESTAQUE!\n\n"
            f"{p['name']}\n"
            f"💰 {p['price']}\n\n"
            f"🛒 Comprar agora:\n{p['url']}"
        )
        send_message(msg)

# =========================
if __name__ == "__main__":
    main()