import os
import json
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import telegram

# =============================
# CONFIGURAÇÃO TELEGRAM
# =============================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", 0))

if not TOKEN or CHAT_ID == 0:
    raise Exception("TELEGRAM_TOKEN ou CHAT_ID não configurados")

bot = telegram.Bot(token=TOKEN)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}

# =============================
# AFILIADOS
# =============================
AFFILIATES = {
    "amazon": "salvablessjj-20",
    "shopee": "18308930971",
    "mercadolivre": "1561730990",
    "netshoes": "rWODdSNWJGM"
}

# =============================
# UTILIDADES
# =============================
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============================
# DADOS
# =============================
categories = load_json("categories.json", [])
copies = load_json("copy.json", {})
history = load_json("history.json", {})

# =============================
# AFILIADO
# =============================
def apply_affiliate(url):
    if "amazon" in url:
        return f"https://www.amazon.com.br{url}?tag={AFFILIATES['amazon']}"
    if "netshoes" in url:
        return f"https://www.netshoes.com.br{url}?utm_source=afiliado&utm_medium=link&utm_campaign={AFFILIATES['netshoes']}"
    return url

# =============================
# SCRAPER
# =============================
def get_products(search_url):
    products = []
    try:
        r = requests.get(search_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            price = 0.0
            price_tag = a.select_one("span.a-offscreen")
            if price_tag:
                try:
                    price = float(
                        price_tag.text.replace("R$", "")
                        .replace(".", "")
                        .replace(",", ".")
                        .strip()
                    )
                except:
                    price = 0.0

            img = a.find("img")
            img_url = img.get("src") if img else ""

            products.append({
                "name": title[:100],
                "price": price,
                "url": a["href"],
                "image": img_url,
                "time": datetime.now().isoformat()
            })

        return products[:10]

    except Exception as e:
        print("[ERRO SCRAPER]", e)
        return []

# =============================
# ENVIO TELEGRAM
# =============================
def send_product(cat, product):
    text = random.choice(
        copies.get(cat.get("niche"), ["🔥 Confira essa oferta:"])
    )

    price_txt = f"💰 R$ {product['price']:.2f}" if product["price"] > 0 else "💰 Consulte o preço"

    msg = (
        f"<b>{cat['category']}</b>\n\n"
        f"{text}\n"
        f"{product['name']}\n"
        f"{price_txt}\n\n"
        f"<a href='{apply_affiliate(product['url'])}'>🔗 Comprar agora</a>"
    )

    bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="HTML",
        disable_web_page_preview=False
    )

# =============================
# EXECUÇÃO PRINCIPAL
# =============================
total_sent = 0

for cat in categories:
    print(f"\n[Categoria] {cat['category']}")
    products = get_products(cat["search_url"])
    print("Produtos encontrados:", len(products))

    sent_this_cat = False

    for p in products:
        old_price = history.get(p["name"], p["price"])
        history[p["name"]] = p["price"]

        # REGRA: oferta OU queda OU potencial
        if p["price"] > 0 and (p["price"] < old_price or random.random() < 0.4):
            send_product(cat, p)
            total_sent += 1
            sent_this_cat = True
            print("[ENVIADO]", p["name"])
            break

    # FALLBACK — SEMPRE ENVIA
    if not sent_this_cat and products:
        p = random.choice(products)
        send_product(cat, p)
        total_sent += 1
        print("[FALLBACK ENVIADO]", p["name"])

# =============================
# GARANTIA FINAL (NUNCA FICA MUDO)
# =============================
if total_sent == 0 and categories:
    cat = random.choice(categories)
    products = get_products(cat["search_url"])
    if products:
        p = random.choice(products)
        send_product(cat, p)
        print("[ENVIO FORÇADO FINAL]")

# =============================
# SALVAR HISTÓRICO
# =============================
save_json("history.json", history)
print("\nExecução finalizada com sucesso")
