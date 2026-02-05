import asyncio
import requests, json, os, random
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# =============================
# ⚡ CONFIGURAÇÃO TELEGRAM
# =============================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", 0))
bot = Bot(token=TOKEN)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# =============================
# ⚡ FUNÇÃO PARA CARREGAR ARQUIVOS JSON
# =============================
def load(file, default):
    return json.load(open(file)) if os.path.exists(file) else default

categories = load("categories.json", [])
history = load("history.json", {})
copies = load("copy.json", {})
affiliates = load("affiliates.json", {})

ranking = []
fallback_counter = 0  # contador para fallback

# =============================
# ⚡ LINK AFILIADO
# =============================
def apply_affiliate(url, niche):
    if "amazon" in url: return affiliates.get("amazon", url)
    if "shopee" in url: return affiliates.get("shopee", url)
    if "mercadolivre" in url: return affiliates.get("mercadolivre", url)
    if "netshoes" in url: return affiliates.get("netshoes", url)
    return url

# =============================
# ⚡ PEGAR PRODUTOS
# =============================
def get_products(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        products = []
        for a in soup.find_all("a", href=True):
            price = a.select_one(".andes-money-amount__fraction, span.a-offscreen")
            title = a.select_one("h2, span.a-text-normal")
            promo = a.select_one(".promotion, .offer, .sale")  # verifica promoção/oferta
            if title:
                try:
                    value = int(price.text.replace(".", "").replace(",", "")) if price else 0
                except:
                    continue
                products.append({
                    "name": title.text.strip()[:80],
                    "price": value,
                    "url": a["href"],
                    "promo": bool(promo),
                    "time": datetime.now().isoformat()
                })
        return products[:15]
    except Exception as e:
        print(f"[Erro get_products] {url} - {e}")
        return []

# =============================
# ⚡ FUNÇÃO PARA ENVIAR MENSAGEM (async)
# =============================
async def send_message(msg):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"[Erro Telegram] {e}")

# =============================
# ⚡ EXECUÇÃO PRINCIPAL
# =============================
async def main():
    global fallback_counter

    for cat in categories:
        print(f"\n[Buscando produtos] Categoria: {cat['category']} | URL: {cat['search_url']}")
        products = get_products(cat["search_url"])
        print(f"Produtos encontrados: {len(products)}")

        eligible = []
        for p in products:
            key = p["name"]
            old_price = history.get(key, p["price"])
            price_drop = old_price - p["price"]  # queda de preço recente

            # Condicional:
            # - Sempre posta Choice
            # - Ou se estiver em promoção/oferta
            # - Ou se tiver potencial de vendas (queda de preço)
            if cat["niche"] == "choice" or p["promo"] or price_drop > 0:
                eligible.append(p)

            # Atualiza histórico
            history[key] = p["price"]

        # Fallback: se não houver produtos elegíveis (exceto Choice)
        if not eligible and cat["niche"] != "choice":
            fallback_counter += 1
            if fallback_counter >= 1:  # 1 execução sem produto → envia 1 produto
                fallback_product = products[0] if products else None
                if fallback_product:
                    eligible.append(fallback_product)
                fallback_counter = 0

        # Envia mensagens
        for p in eligible:
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            msg = f"{text}\n{p['name']}\n💰 R$ {p['price']}\n{link}"
            print(f"[Enviando] {msg}")
            await send_message(msg)
            score = price_drop  # ranking simples
            ranking.append((score, p))

    # Ranking diário
    ranking.sort(reverse=True, key=lambda x: x[0])
    if ranking:
        msg = "🏆 TOP OFERTAS DO DIA\n\n"
        for i, (_, p) in enumerate(ranking[:5], 1):
            msg += f"{i}️⃣ {p['name']} – R$ {p['price']}\n"
        print(f"[Enviando Ranking]\n{msg}")
        await send_message(msg)

    # Salva histórico
    json.dump(history, open("history.json", "w"))
    print("\n[Histórico salvo]")

# =============================
# ⚡ EXECUTA O BOT
# =============================
if __name__ == "__main__":
    asyncio.run(main())
