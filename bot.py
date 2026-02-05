import requests, json, os, random
from bs4 import BeautifulSoup
import telegram

# =============================
# ⚡ CONFIGURAÇÃO TELEGRAM
# =============================
TOKEN = os.environ["TELEGRAM_TOKEN"]  # Adicione nos Secrets do GitHub
CHAT_ID = os.environ["CHAT_ID"]        # Adicione nos Secrets do GitHub
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
# ⚡ BUSCA AUTOMÁTICA DE CUPONS
# =============================
def fetch_coupons(niche, site_url):
    """Busca cupons ativos na página do site e atualiza JSON automaticamente"""
    cupons = []
    try:
        r = requests.get(site_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        # Exemplo: cupons dentro de spans com class "coupon-code"
        for tag in soup.find_all("span", class_="coupon-code"):
            code = tag.text.strip()
            if code: cupons.append(code)
    except:
        pass
    # Atualiza JSON do nicho
    if cupons:
        with open(f"coupons_{niche}.json","w") as f:
            json.dump(cupons,f)
    return cupons

def get_coupon(niche, site_url):
    """Pega um cupom aleatório, atualizando antes"""
    fetch_coupons(niche, site_url)
    try:
        with open(f"coupons_{niche}.json","r") as f:
            cupons = json.load(f)
            return random.choice(cupons) if cupons else ""
    except:
        return ""

# =============================
# ⚡ FUNÇÃO PARA PEGAR PRODUTOS
# =============================
def get_products(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    products = []
    for a in soup.find_all("a", href=True):
        price = a.select_one(".andes-money-amount__fraction, span.a-offscreen")
        title = a.select_one("h2, span.a-text-normal")
        if price and title:
            try:
                value = int(price.text.replace(".", "").replace(",", ""))
            except:
                continue
            products.append({"name": title.text.strip()[:80], "price": value, "url": a["href"]})
    return products[:15]

# =============================
# ⚡ LOOP PRINCIPAL
# =============================
for cat in categories:
    products = get_products(cat["search_url"])
    for p in products:
        key = p["name"]
        old_price = history.get(key, p["price"])
        discount = round((old_price - p["price"]) / old_price * 100, 1) if old_price else 0
        score = discount*2 + (old_price - p["price"])

        if discount >= cat["min_discount"]:
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            cupom = get_coupon(cat["niche"], cat["search_url"])
            cupom_text = f"\n🎫 Use o cupom: {cupom}" if cupom else ""
            bot.send_message(CHAT_ID, f"{text}\n{p['name']}\n💰 R$ {p['price']} (-{discount}%)\n{link}{cupom_text}")
            ranking.append((score,p))

        history[key] = p["price"]

# =============================
# ⚡ RANKING DIÁRIO
# =============================
ranking.sort(reverse=True,key=lambda x:x[0])
if ranking:
    msg="🏆 TOP OFERTAS DO DIA\n\n"
    for i,(_,p) in enumerate(ranking[:5],1):
        msg+=f"{i}️⃣ {p['name']} – R$ {p['price']}\n"
    bot.send_message(CHAT_ID,msg)

# =============================
# ⚡ SALVAR HISTÓRICO
# =============================
json.dump(history,open("history.json","w"))
