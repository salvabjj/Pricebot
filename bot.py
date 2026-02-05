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

POSTS_POR_EXECUCAO = 3

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
# SCRAPER AMAZON
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

        return products[:20]

    except Exception as e:
        print("[ERRO SCRAPER]", e)
        return []

# =============================
# EXECUÇÃO PRINCIPAL
# =============================
todos_produtos = []
produtos_prioritarios = []

for cat in categories:
    print(f"[Categoria] {cat['category']}")
    encontrados = get_products(cat["search_url"])
    print(f"Encontrados: {len(encontrados)}")

    todos_produtos.extend(encontrados)

    for p in encontrados:
        nome = p["name"]
        preco_atual = p["price"]
        preco_antigo = history.get(nome)

        # Produto novo OU preço mudou
        if nome not in history or (preco_antigo and preco_atual != preco_antigo):
            produtos_prioritarios.append(p)

# Remove duplicados
def unique_by_name(lista):
    vistos = set()
    resultado = []
    for p in lista:
        if p["name"] not in vistos:
            vistos.add(p["name"])
            resultado.append(p)
    return resultado

produtos_prioritarios = unique_by_name(produtos_prioritarios)
todos_produtos = unique_by_name(todos_produtos)

# Seleção final
selecionados = produtos_prioritarios[:POSTS_POR_EXECUCAO]

if len(selecionados) < POSTS_POR_EXECUCAO:
    restantes = POSTS_POR_EXECUCAO - len(selecionados)
    aleatorios = random.sample(
        [p for p in todos_produtos if p not in selecionados],
        k=min(restantes, len(todos_produtos))
    )
    selecionados.extend(aleatorios)

# =============================
# ENVIO GARANTIDO (3)
# =============================
enviados = 0

for p in selecionados:
    link = apply_affiliate(p["url"])
    preco_txt = f"R$ {p['price']:.2f}" if p["price"] > 0 else "Consulte o preço"

    msg = (
        f"🔥 OFERTA EM DESTAQUE!\n\n"
        f"{p['name']}\n"
        f"💰 {preco_txt}\n"
        f"🔗 Comprar agora:\n{link}"
    )

    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
        enviados += 1
        print("[Enviado]", p["name"])
    except Exception as e:
        print("[Erro Telegram]", e)

    history[p["name"]] = p["price"]

print(f"\n[OK] Total enviado: {enviados}")

# =============================
# SALVAR HISTÓRICO
# =============================
save_json("history.json", history)