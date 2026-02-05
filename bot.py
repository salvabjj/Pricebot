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
# ⚡ FUNÇÃO PARA CARREGAR ARQUIVOS JSON
# =============================
def load(file, default):
    return json.load(open(file)) if os.path.exists(file) else default

categories = load("categories.json", [])
history = load("history.json", {})
copies = load("copy.json", {})
affiliates = load("affiliates.json", {})

ranking = []

# =============================
# ⚡ APLICAR LINK AFILIADO
# =============================
def apply_affiliate(url, niche):
    if "amazon" in url: return affiliates.get("amazon", url)
    if "shopee" in url: return affiliates.get("shopee", url)
    if "mercadolivre" in url: return affiliates.get("mercadolivre", url)
    if "netshoes" in url: return affiliates.get("netshoes", url)
    return url

# =============================
# ⚡ BUSCA AUTOMÁTICA DE CUPONS
# =============================
def fetch_coupons(niche, site_url):
    cupons = []
    try:
        r = requests.get(site_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all("span", class_="coupon-code"):
            code = tag.text.strip()
            if code: cupons.append(code)
    except Exception as e:
        print(f"[Erro cupom] {niche} - {e}")
    if cupons:
        with open(f"coupons_{niche}.json", "w") as f:
            json.dump(cupons, f)
    return cupons

def get_coupon(niche, site_url):
    cupons = fetch_coupons(niche, site_url)
    try:
        with open(f"coupons_{niche}.json", "r") as f:
            cupons_file = json.load(f)
            all_coupons = cupons + cupons_file
            return random.choice(all_coupons) if all_coupons else ""
    except:
        return ""  # Retorna vazio se não houver

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
            promo = a.select_one(".promotion-badge, .offer-label")
            if price and title:
                try:
                    value = int(price.text.replace(".", "").replace(",", ""))
                except:
                    continue
                products.append({
                    "name": title.text.strip()[:80],
                    "price": value,
                    "url": a["href"],
                    "promotion": bool(promo),
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
    print(f"\n[Buscando produtos] Categoria: {cat['category']} | URL: {cat['search_url']}")
    products = get_products(cat["search_url"])
    print(f"Produtos encontrados: {len(products)}")

    for p in products:
        key = p["name"]
        old_price = history.get(key, p["price"])
        discount = round((old_price - p["price"]) / old_price * 100, 1) if old_price else 0
        price_drop = old_price - p["price"]
        score = discount*2 + price_drop

        # Condicional: promo, oferta, queda ou potencial de venda
        if p["promotion"] or price_drop > 0 or discount >= 5:
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            cupom = get_coupon(cat["niche"], cat["search_url"])
            cupom_text = f"\n🎫 Use o cupom: {cupom}" if cupom else ""

            msg = f"{text}\n{p['name']}\n💰 R$ {p['price']} (-{discount}%)\n{link}{cupom_text}"
            print(f"[Enviando] {msg}")
            try:
                bot.send_message(CHAT_ID, msg)
            except Exception as e:
                print(f"[Erro Telegram] {e}")

            ranking.append((score, p))
        else:
            print(f"[Ignorado] {p['name']} - Desconto: {discount}% | Queda: {price_drop} | Promo: {p['promotion']}")

        history[key] = p["price"]

# =============================
# ⚡ RANKING DIÁRIO
# =============================
ranking.sort(reverse=True,key=lambda x:x[0])
if ranking:
    msg = "🏆 TOP OFERTAS DO DIA\n\n"
    for i,(_,p) in enumerate(ranking[:5], 1):
        msg += f"{i}️⃣ {p['name']} – R$ {p['price']}\n"
    print(f"[Enviando Ranking]\n{msg}")
    try:
        bot.send_message(CHAT_ID, msg)
    except Exception as e:
        print(f"[Erro Telegram Ranking] {e}")

# =============================
# ⚡ SALVAR HISTÓRICO
# =============================
json.dump(history, open("history.json","w"))
print("\n[Histórico salvo]")
