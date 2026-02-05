import os
import json
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import telegram

# =============================
# CONFIG TELEGRAM
# =============================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", 0))
bot = telegram.Bot(token=TOKEN)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

POSTS_POR_EXECUCAO = 3

# =============================
# AFILIADOS
# =============================
AFFILIATES = {
    "amazon": "salvablessjj-20",
    "netshoes": "https://www.netshoes.com.br/afiliado/rWODdSNWJGM",
    "zattini": "https://www.zattini.com.br/",
    "mercadolivre": "https://www.mercadolivre.com.br/",
    "shopee": "https://shopee.com.br/"
}

# =============================
# JSON HELPERS
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
fallback_cache = load_json("fallback_products.json", [])

# =============================
# AFILIADO LINK
# =============================
def apply_affiliate(url, site):
    if site == "amazon":
        if not url.startswith("http"):
            url = "https://www.amazon.com.br" + url
        if "tag=" not in url:
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}tag={AFFILIATES['amazon']}"
    return url

# =============================
# FALLBACK CACHE
# =============================
def save_fallback(products, limit=200):
    global fallback_cache
    for p in products:
        if not any(fp["name"] == p["name"] for fp in fallback_cache):
            fallback_cache.append(p)
    fallback_cache = fallback_cache[-limit:]
    save_json("fallback_products.json", fallback_cache)

def get_fallback(qtd):
    if not fallback_cache:
        return []
    return random.sample(fallback_cache, min(qtd, len(fallback_cache)))

# =============================
# SCRAPER AMAZON
# =============================
def scrape_amazon(url):
    products = []
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    cards = soup.select("div[data-component-type='s-search-result']")
    for c in cards:
        title = c.select_one("h2 a span")
        price = c.select_one("span.a-offscreen")
        link = c.select_one("h2 a")

        if not title or not link:
            continue

        name = title.text.strip()
        if len(name) < 15:
            continue

        value = 0.0
        if price:
            try:
                value = float(price.text.replace("R$", "").replace(".", "").replace(",", "."))
            except:
                pass

        products.append({
            "name": name[:120],
            "price": value,
            "url": link["href"],
            "site": "amazon"
        })

    return products

# =============================
# SCRAPER GENÉRICO
# =============================
def scrape_generic(url, site):
    products = []
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        name = a.text.strip()
        if len(name) < 20:
            continue

        products.append({
            "name": name[:120],
            "price": 0.0,
            "url": a["href"] if a["href"].startswith("http") else url,
            "site": site
        })

    return products[:20]

# =============================
# COLETA
# =============================
todos = []
prioritarios = []

for cat in categories:
    site = cat["site"]
    print(f"[Categoria] {cat['category']} ({site})")

    try:
        if site == "amazon":
            produtos = scrape_amazon(cat["search_url"])
        else:
            produtos = scrape_generic(cat["search_url"], site)
    except Exception as e:
        print("[Erro scraper]", e)
        produtos = []

    print("Encontrados:", len(produtos))
    todos.extend(produtos)
    save_fallback(produtos)

    for p in produtos:
        nome = p["name"]
        preco = p["price"]
        antigo = history.get(nome)

        if nome not in history or (antigo and preco != antigo):
            prioritarios.append(p)

# =============================
# SELEÇÃO FINAL
# =============================
def unique(lista):
    seen = set()
    out = []
    for p in lista:
        if p["name"] not in seen:
            seen.add(p["name"])
            out.append(p)
    return out

todos = unique(todos)
prioritarios = unique(prioritarios)

selecionados = prioritarios[:POSTS_POR_EXECUCAO]

if len(selecionados) < POSTS_POR_EXECUCAO:
    faltam = POSTS_POR_EXECUCAO - len(selecionados)
    pool = [p for p in todos if p not in selecionados]
    selecionados.extend(random.sample(pool, min(faltam, len(pool))))

# =============================
# FALLBACK REAL
# =============================
if len(selecionados) < POSTS_POR_EXECUCAO:
    faltam = POSTS_POR_EXECUCAO - len(selecionados)
    selecionados.extend(get_fallback(faltam))

# =============================
# ENVIO
# =============================
enviados = 0

for p in selecionados:
    link = apply_affiliate(p["url"], p["site"])
    preco = f"R$ {p['price']:.2f}" if p["price"] > 0 else "Consulte o preço"

    msg = (
        f"🔥 OFERTA EM DESTAQUE!\n\n"
        f"{p['name']}\n"
        f"💰 {preco}\n"
        f"🔗 Comprar agora:\n{link}"
    )

    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
        enviados += 1
        history[p["name"]] = p["price"]
    except Exception as e:
        print("[Erro Telegram]", e)

print("[Total enviados]", enviados)

save_json("history.json", history)