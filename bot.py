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

bot = telegram.Bot(token=TOKEN)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# =============================
# AFILIADOS
# =============================
AFFILIATES = {
    "amazon": "salvablessjj-20"
}

# =============================
# UTILIDADES JSON
# =============================
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

categories = load_json("categories.json", [])
history = load_json("history.json", {})

# =============================
# LINK AFILIADO AMAZON
# =============================
def apply_affiliate(url):
    if "amazon.com.br" in url and "tag=" not in url:
        sep = "&" if "?" in url else "?"
        return f"https://www.amazon.com.br{url}{sep}tag={AFFILIATES['amazon']}"
    return url

# =============================
# SCRAPER AMAZON (CORRIGIDO)
# =============================
def get_products(search_url):
    products = []

    try:
        r = requests.get(search_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        cards = soup.select("div[data-component-type='s-search-result']")

        for card in cards:
            title_tag = card.select_one("h2 a span")
            price_tag = card.select_one("span.a-offscreen")
            link_tag = card.select_one("h2 a")
            img_tag = card.select_one("img")

            if not title_tag or not link_tag:
                continue

            name = title_tag.text.strip()
            if len(name) < 15:
                continue

            price = 0.0
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

            products.append({
                "name": name[:120],
                "price": price,
                "url": link_tag["href"],
                "image": img_tag["src"] if img_tag else "",
                "time": datetime.now().isoformat()
            })

        return products[:10]

    except Exception as e:
        print("[ERRO SCRAPER]", e)
        return []

# =============================
# EXECUÇÃO PRINCIPAL
# =============================
total_enviados = 0
todos_produtos = []

for cat in categories:
    print(f"\n[Categoria] {cat['category']}")
    produtos = get_products(cat["search_url"])
    print(f"Encontrados: {len(produtos)}")

    todos_produtos.extend(produtos)

    for p in produtos:
        nome = p["name"]
        preco_atual = p["price"]
        preco_antigo = history.get(nome)

        postar = False

        # Se tiver histórico e preço mudou
        if preco_antigo and preco_atual > 0 and preco_atual != preco_antigo:
            postar = True

        # Se não tiver histórico (produto novo)
        if nome not in history:
            postar = True

        if postar:
            link = apply_affiliate(p["url"])
            preco_txt = f"R$ {preco_atual:.2f}" if preco_atual > 0 else "Consulte o preço"

            msg = (
                f"🔥 OFERTA ENCONTRADA!\n\n"
                f"{nome}\n"
                f"💰 {preco_txt}\n"
                f"🔗 Comprar agora:\n{link}"
            )

            try:
                bot.send_message(chat_id=CHAT_ID, text=msg)
                total_enviados += 1
                print("[Enviado]", nome)
            except Exception as e:
                print("[Erro Telegram]", e)

            history[nome] = preco_atual

            if total_enviados >= 1:
                break

    if total_enviados >= 1:
        break

# =============================
# FALLBACK – SEMPRE ENVIA 1
# =============================
if total_enviados == 0 and todos_produtos:
    p = random.choice(todos_produtos)
    link = apply_affiliate(p["url"])
    preco_txt = f"R$ {p['price']:.2f}" if p["price"] > 0 else "Consulte o preço"

    msg = (
        f"✨ DESTAQUE DO DIA!\n\n"
        f"{p['name']}\n"
        f"💰 {preco_txt}\n"
        f"🔗 Comprar agora:\n{link}"
    )

    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
        print("[Fallback enviado]")
    except Exception as e:
        print("[Erro Telegram fallback]", e)

# =============================
# SALVAR HISTÓRICO
# =============================
save_json("history.json", history)
print("\n[OK] Execução finalizada")
