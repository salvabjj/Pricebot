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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

POSTS_PER_RUN = 3
CACHE_FILE = "product_cache.json"

AMAZON_TAG = "salvablessjj-20"

# =========================
# UTIL
# =========================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
# AMAZON SCRAPER
# =========================
def scrape_amazon(query):
    url = f"https://www.amazon.com.br/s?k={query.replace(' ', '+')}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    products = []

    for item in soup.select("div[data-component-type='s-search-result']"):
        title = item.select_one("h2 span")
        link = item.select_one("h2 a")
        price = item.select_one("span.a-offscreen")

        if not title or not link:
            continue

        href = link.get("href", "")
        if "dp/" not in href:
            continue

        name = title.text.strip()
        price_text = price.text.strip() if price else "Consulte o preço"

        full_link = f"https://www.amazon.com.br{href}"
        if "tag=" not in full_link:
            sep = "&" if "?" in full_link else "?"
            full_link += f"{sep}tag={AMAZON_TAG}"

        products.append({
            "name": name,
            "price": price_text,
            "url": full_link,
            "site": "amazon"
        })

    return products

# =========================
# MAIN
# =========================
def main():
    cache = load_json(CACHE_FILE)

    queries = [
        "tenis esportivo",
        "moda masculina",
        "moda feminina",
        "moda infantil",
        "suplementos"
    ]

    found_products = []

    for q in queries:
        try:
            found_products.extend(scrape_amazon(q))
        except Exception as e:
            print("Erro Amazon:", e)

    # =========================
    # SE ACHOU PRODUTOS → SALVA
    # =========================
    if found_products:
        for p in found_products:
            if not any(c["url"] == p["url"] for c in cache):
                cache.append(p)

        cache = cache[-200:]  # limita cache
        save_json(CACHE_FILE, cache)

        random.shuffle(found_products)
        selected = found_products[:POSTS_PER_RUN]

    # =========================
    # SE NÃO ACHOU → FALLBACK
    # =========================
    else:
        if not cache:
            send_message("⚠️ Cache vazio. Aguardando próxima execução.")
            return

        random.shuffle(cache)
        selected = cache[:POSTS_PER_RUN]

    # =========================
    # ENVIO
    # =========================
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