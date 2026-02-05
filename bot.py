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
# ⚡ LINKS DE AFILIADOS
# =============================
affiliates = {
    "amazon": "salvablessjj-20",
    "shopee": "18308930971",
    "mercadolivre": "1561730990",
    "netshoes": "rWODdSNWJGM"
}

# =============================
# ⚡ FUNÇÃO PARA CARREGAR JSON
# =============================
def load(file, default):
    return json.load(open(file)) if os.path.exists(file) else default

categories = load("categories.json", [])
history = load("history.json", {})
copies = load("copy.json", {})

fallback_counter = 0

# =============================
# ⚡ APLICAR LINK DE AFILIADO
# =============================
def apply_affiliate(url, niche):
    if "amazon" in url:
        return f"{url}?tag={affiliates.get('amazon','')}"
    if "shopee" in url:
        return f"https://shopee.com.br/universal-link/{affiliates.get('shopee','')}"
    if "mercadolivre" in url:
        return f"https://www.mercadolivre.com.br/affiliates/{affiliates.get('mercadolivre','')}"
    if "netshoes" in url:
        return f"https://www.netshoes.com.br/afiliado/{affiliates.get('netshoes','')}"
    return url

# =============================
# ⚡ BUSCAR CUPONS AUTOMÁTICOS
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
        return ""

# =============================
# ⚡ PEGAR PRODUTOS
# =============================
def get_products(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        products = []
        for a in soup.find_all("a", href=True):
            title_tag = a.select_one("h2, span.a-text-normal")
            name = title_tag.text.strip()[:80] if title_tag else None

            price_tag = a.select_one(".andes-money-amount__fraction, span.a-offscreen")
            try:
                price = float(price_tag.text.replace("R$", "").replace(".", "").replace(",", ".")) if price_tag else 0
            except:
                price = 0

            img_tag = a.select_one("img")
            image_url = img_tag.get('data-src') or img_tag.get('src') or "https://via.placeholder.com/300"

            offer = False
            if a.select_one(".promotion, .offer-badge, .sale-badge"):
                offer = True

            if name:
                products.append({
                    "name": name,
                    "price": price,
                    "url": a["href"],
                    "image": image_url,
                    "offer": offer,
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

    sent_any = False

    # ✅ Enviar sempre Choice
    for p in products:
        if cat.get("niche") == "choice":
            text = random.choice(copies.get(cat["niche"], ["✨ Produto em destaque:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            cupom = get_coupon(cat["niche"], cat["search_url"])
            cupom_text = f"🎫 Use o cupom: {cupom}" if cupom else ""
            msg_price = f"💰 R$ {p['price']:.2f}"

            msg = f"""<b>{cat['category']} EM DESTAQUE!</b>
{text}
{p['name']}
{msg_price}
<a href="{p['image']}">📷 Imagem</a>
<a href="{link}">🔗 Link de Compra</a>
{cupom_text}"""

            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML", disable_web_page_preview=False)
                sent_any = True
                print(f"[Choice Enviado] {p['name']}")
            except Exception as e:
                print(f"[Erro Telegram Choice] {e}")

    # ✅ Enviar ofertas ou produtos com potencial
    for p in products:
        key = p["name"]
        old_price = history.get(key, p["price"])
        price_diff = old_price - p["price"]

        # Condição: oferta ou queda de preço ou potencial de vendas
        if cat.get("niche") != "choice" and (p["offer"] or price_diff>0):
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            cupom = get_coupon(cat["niche"], cat["search_url"])
            cupom_text = f"🎫 Use o cupom: {cupom}" if cupom else ""
            msg_price = f"💰 R$ {p['price']:.2f}"
            if price_diff > 0:
                msg_price += f" (↓ R$ {price_diff:.2f})"

            msg = f"""<b>{cat['category']} EM OFERTA!</b>
{text}
{p['name']}
{msg_price}
<a href="{p['image']}">📷 Imagem</a>
<a href="{link}">🔗 Link de Compra</a>
{cupom_text}"""

            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML", disable_web_page_preview=False)
                sent_any = True
                print(f"[Oferta Enviada] {p['name']}")
            except Exception as e:
                print(f"[Erro Telegram] {e}")

        history[key] = p["price"]

    # ✅ Fallback se nada enviado (exceto Choice)
    if not sent_any:
        fallback_counter += 1
        for p in products:
            if cat.get("niche") == "choice":
                continue
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            msg_price = f"💰 R$ {p['price']:.2f}"
            msg = f"<b>{cat['category']} EM OFERTA!</b>\n{text}\n{p['name']}\n{msg_price}\n<a href='{link}'>🔗 Link de Compra</a>"
            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML", disable_web_page_preview=False)
                print(f"[Fallback Enviado] {p['name']}")
            except Exception as e:
                print(f"[Erro Telegram fallback] {e}")
            fallback_counter = 0
            break

# =============================
# ⚡ RANKING DIÁRIO
# =============================
ranking.sort(reverse=True,key=lambda x:x[0])
if ranking:
    msg = "🏆 TOP OFERTAS DO DIA\n\n"
    for i,(_,p) in enumerate(ranking[:5], 1):
        msg += f"{i}️⃣ {p['name']} – R$ {p['price']:.2f}\n"
    try:
        bot.send_message(CHAT_ID, msg)
    except Exception as e:
        print(f"[Erro Telegram Ranking] {e}")

# =============================
# ⚡ SALVAR HISTÓRICO
# =============================
json.dump(history, open("history.json","w"))
print("\n[Histórico salvo]")
