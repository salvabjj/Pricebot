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
# ⚡ FUNÇÃO DE PARSE DE PREÇO POR SITE
# =============================
def parse_price(a, site_url):
    try:
        if "amazon" in site_url:
            el = a.select_one("span.a-offscreen")
        elif "shopee" in site_url:
            el = a.select_one("div._1w9jLI.QbH7Ig._1VfKBz")
        elif "mercadolivre" in site_url:
            el = a.select_one(".price-tag-fraction")
        elif "netshoes" in site_url:
            el = a.select_one(".productPrice")
        else:
            el = None
        if el:
            text = el.text.strip().replace(".", "").replace(",", "")
            return int(''.join(filter(str.isdigit, text)))
    except:
        pass
    return 0

# =============================
# ⚡ LINK AFILIADO
# =============================
def apply_affiliate(url, niche):
    if "amazon" in url:
        tag = affiliates.get("amazon", "SEUTAG-20")
        try:
            asin = url.split("/dp/")[1].split("/")[0]
            return f"https://www.amazon.com.br/dp/{asin}/?tag={tag}"
        except:
            return url
    if "shopee" in url:
        return f"{affiliates.get('shopee', '')}?{url.split('m/choice')[-1]}"
    if "mercadolivre" in url:
        return f"{url}?m={affiliates.get('mercadolivre', '')}"
    if "netshoes" in url:
        return f"{url}?af={affiliates.get('netshoes', '')}"
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
            price = parse_price(a, url)
            title = a.select_one("h2, span.a-text-normal")
            img_tag = a.select_one("img")
            image_url = img_tag['src'] if img_tag else ""
            offer_tag = a.select_one(".offer, .promo, .badge-offer")  # Marcação de promoção
            is_offer = bool(offer_tag)
            if price and title:
                products.append({
                    "name": title.text.strip()[:80],
                    "price": price,
                    "url": a["href"],
                    "image": image_url,
                    "offer": is_offer,
                    "time": datetime.now().isoformat()
                })
        return products[:15]
    except Exception as e:
        print(f"[Erro get_products] {url} - {e}")
        return []

# =============================
# ⚡ EXECUÇÃO PRINCIPAL
# =============================
fallback_counter = 0  # Contador para fallback se não encontrar produtos

for cat in categories:
    print(f"\n[Buscando produtos] Categoria: {cat['category']} | URL: {cat['search_url']}")
    products = get_products(cat["search_url"])
    print(f"Produtos encontrados: {len(products)}")

    for p in products:
        key = p["name"]
        old_price = history.get(key, p["price"])
        price_drop = old_price - p["price"]
        score = price_drop

        post_product = p["offer"] or cat["niche"] == "choice" or score > 0

        if post_product:
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            cupom = get_coupon(cat["niche"], cat["search_url"])
            cupom_text = f"\n🎫 Use o cupom: {cupom}" if cupom else ""
            msg = f"{text}\n{p['name']}\n💰 R$ {p['price']}\n{link}{cupom_text}"
            try:
                if p["image"]:
                    bot.send_photo(chat_id=CHAT_ID, photo=p["image"], caption=msg)
                else:
                    bot.send_message(chat_id=CHAT_ID, text=msg)
            except Exception as e:
                print(f"[Erro Telegram] {e}")
            ranking.append((score, p))
        else:
            fallback_counter += 1
            print(f"[Ignorado] {p['name']} - Sem promoção e sem queda")

        # Atualiza histórico
        history[key] = p["price"]

# =============================
# ⚡ Fallback: postar se não houver produtos suficientes (desconsiderando Choice)
# =============================
if fallback_counter >= 1:
    for cat in categories:
        if cat["niche"] != "choice":
            products = get_products(cat["search_url"])
            for p in products[:2]:  # Posta os dois primeiros como fallback
                text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
                link = apply_affiliate(p["url"], cat["niche"])
                cupom = get_coupon(cat["niche"], cat["search_url"])
                cupom_text = f"\n🎫 Use o cupom: {cupom}" if cupom else ""
                msg = f"{text}\n{p['name']}\n💰 R$ {p['price']}\n{link}{cupom_text}"
                try:
                    if p["image"]:
                        bot.send_photo(chat_id=CHAT_ID, photo=p["image"], caption=msg)
                    else:
                        bot.send_message(chat_id=CHAT_ID, text=msg)
                except Exception as e:
                    print(f"[Erro Telegram fallback] {e}")

# =============================
# ⚡ RANKING DIÁRIO
# =============================
ranking.sort(reverse=True,key=lambda x:x[0])
if ranking:
    msg = "🏆 TOP OFERTAS DO DIA\n\n"
    for i,(_,p) in enumerate(ranking[:5], 1):
        msg += f"{i}️⃣ {p['name']} – R$ {p['price']}\n"
    try:
        bot.send_message(CHAT_ID, msg)
    except Exception as e:
        print(f"[Erro Telegram Ranking] {e}")

# =============================
# ⚡ SALVAR HISTÓRICO
# =============================
json.dump(history, open("history.json", "w"))
print("\n[Histórico salvo]")
