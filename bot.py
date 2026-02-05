import requests, json, os, random
from bs4 import BeautifulSoup
import telegram
from datetime import datetime

# =============================
# ⚡ CONFIGURAÇÃO TELEGRAM
# =============================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", 0))
bot = telegram.Bot(token=TOKEN)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# =============================
# ⚡ CARREGAR ARQUIVOS JSON
# =============================
def load(file, default):
    try:
        return json.load(open(file))
    except:
        return default

categories = load("categories.json", [])
history = load("history.json", {})
copies = load("copy.json", {})
affiliates = load("affiliates.json", {})

ranking = []

# =============================
# ⚡ LINK AFILIADO
# =============================
def apply_affiliate(url, niche):
    try:
        if "amazon" in url: return affiliates.get("amazon", url)
        if "shopee" in url: return affiliates.get("shopee", url)
        if "mercadolivre" in url: return affiliates.get("mercadolivre", url)
        if "netshoes" in url: return affiliates.get("netshoes", url)
        return url
    except:
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
            price_tag = a.select_one(".andes-money-amount__fraction, span.a-offscreen")
            title_tag = a.select_one("h2, span.a-text-normal")
            promo_tag = a.select_one(".promotion-badge, .offer-label")
            if price_tag and title_tag:
                try:
                    price = int(price_tag.text.replace(".", "").replace(",", ""))
                except:
                    continue
                products.append({
                    "name": title_tag.text.strip()[:80],
                    "price": price,
                    "url": a["href"],
                    "promotion": bool(promo_tag),
                    "time": datetime.now().isoformat()
                })
        return products[:15]
    except Exception as e:
        print(f"[Erro get_products] {url} - {e}")
        return []

# =============================
# ⚡ EXECUÇÃO PRINCIPAL
# =============================
for cat in categories:
    try:
        print(f"\n[Buscando produtos] Categoria: {cat['category']} | URL: {cat['search_url']}")
        products = get_products(cat["search_url"])
        print(f"Produtos encontrados: {len(products)}")
    except Exception as e:
        print(f"[Erro ao buscar categoria] {cat['category']} - {e}")
        continue

    for p in products:
        try:
            key = p["name"]
            old_price = history.get(key, p["price"])
            price_drop = old_price - p["price"]  # queda de preço recente
            score = price_drop  # pontuação baseada na queda

            # Condicional: promoção, queda ou potencial de venda
            if p["promotion"] or price_drop > 0:
                text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
                link = apply_affiliate(p["url"], cat["niche"])
                msg = f"{text}\n{p['name']}\n💰 R$ {p['price']}\n{link}"
                print(f"[Enviando] {msg}")
                try:
                    bot.send_message(CHAT_ID, msg)
                except Exception as e:
                    print(f"[Erro Telegram] {e}")
                ranking.append((score, p))

            # Atualiza histórico
            history[key] = p["price"]
        except Exception as e:
            print(f"[Erro produto] {p.get('name', 'N/A')} - {e}")

# =============================
# ⚡ RANKING DIÁRIO
# =============================
try:
    ranking.sort(reverse=True,key=lambda x:x[0])
    if ranking:
        msg = "🏆 TOP OFERTAS DO DIA\n\n"
        for i,(_,p) in enumerate(ranking[:5],1):
            msg += f"{i}️⃣ {p['name']} – R$ {p['price']}\n"
        print(f"[Enviando Ranking]\n{msg}")
        bot.send_message(CHAT_ID,msg)
except Exception as e:
    print(f"[Erro Ranking] {e}")

# =============================
# ⚡ SALVAR HISTÓRICO
# =============================
try:
    json.dump(history, open("history.json","w"))
    print("[Histórico salvo]")
except Exception as e:
    print(f"[Erro ao salvar histórico] {e}")
