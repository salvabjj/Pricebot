import requests, json, os, random, sys
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
            promo_tag = a.select_one(".promo, .badge-promotion")
            offer_tag = a.select_one(".offer, .badge-offer")
            best_seller_tag = a.select_one(".best-seller, .badge-bestseller")
            if price and title:
                try:
                    value = int(price.text.replace(".", "").replace(",", ""))
                except:
                    continue
                products.append({
                    "name": title.text.strip()[:80],
                    "price": value,
                    "url": a["href"],
                    "time": datetime.now().isoformat(),
                    "promotion": bool(promo_tag),
                    "offer": bool(offer_tag),
                    "best_seller": bool(best_seller_tag)
                })
        return products[:15]
    except Exception as e:
        print(f"[Erro get_products] {url} - {e}")
        return []

# =============================
# ⚡ BUSCA CUPOM (automatizado)
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
# ⚡ EXECUÇÃO PRINCIPAL
# =============================
for cat in categories:
    print(f"\n[Buscando produtos] Categoria: {cat['category']} | URL: {cat['search_url']}")
    products = get_products(cat["search_url"])
    print(f"[Encontrados] {len(products)} produtos na categoria {cat['category']}")

    for p in products:
        key = p["name"]
        old_price = history.get(key, p["price"])
        price_drop = old_price - p["price"]
        score = price_drop  # pontuação baseada na queda de preço

        # ⚡ Condicional de postagem:
        # 1) Queda de preço
        # 2) Promoção
        # 3) Oferta
        # 4) Produto com bom histórico de vendas (best_seller)
        if price_drop > 0 or p.get("promotion", False) or p.get("offer", False) or p.get("best_seller", False):
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            cupom = get_coupon(cat["niche"], cat["search_url"])
            cupom_text = f"\n🎫 Use o cupom: {cupom}" if cupom else ""
            msg = f"{text}\n{p['name']}\n💰 R$ {p['price']}\n{link}{cupom_text}"

            print(f"[Enviando Telegram] {msg}")
            try:
                bot.send_message(CHAT_ID, msg)
            except Exception as e:
                print(f"[Erro Telegram] {e}")

            ranking.append((score, p))
        else:
            print(f"[Ignorado] {p['name']} | Queda: {price_drop} | Promo: {p.get('promotion', False)} | Offer: {p.get('offer', False)} | BestSeller: {p.get('best_seller', False)}")

        # Atualiza histórico
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
