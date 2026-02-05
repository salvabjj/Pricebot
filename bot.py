import requests, json, os, random
from bs4 import BeautifulSoup
import telegram

# TOKEN e CHAT_ID do Telegram
TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

bot = telegram.Bot(token=TOKEN)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Função para carregar arquivos JSON
def load(file, default):
    return json.load(open(file)) if os.path.exists(file) else default

# Carrega arquivos
categories = load("categories.json", [])
history = load("history.json", {})
copies = load("copy.json", {})
affiliates = load("affiliates.json", {})

ranking = []

# Função que aplica o link afiliado
def apply_affiliate(url):
    if "amazon" in url: return affiliates.get("amazon", url)
    if "shopee" in url: return affiliates.get("shopee", url)
    if "mercadolivre" in url: return affiliates.get("mercadolivre", url)
    if "netshoes" in url: return affiliates.get("netshoes", url)
    return url

# Função que pega produtos de uma URL
def get_products(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    products = []
    for a in soup.find_all("a", href=True):
        price = a.select_one(".andes-money-amount__fraction, span.a-offscreen")
        title = a.select_one("h2, span.a-text-normal")
        if price and title:
            try: value = int(price.text.replace(".", "").replace(",", ""))
            except: continue
            products.append({"name": title.text.strip()[:80], "price": value, "url": a["href"]})
    return products[:15]

# Loop principal
for cat in categories:
    products = get_products(cat["search_url"])
    for p in products:
        key = p["name"]
        old_price = history.get(key, p["price"])
        discount = round((old_price - p["price"]) / old_price * 100, 1) if old_price else 0
        score = discount*2 + (old_price - p["price"])

        if discount >= cat["min_discount"] and p["price"] <= cat["max_price"] and score >= 60:
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"])
            bot.send_message(CHAT_ID, f"{text}\n{p['name']}\n💰 R$ {p['price']} (-{discount}%)\n{link}")
            ranking.append((score,p))

        history[key] = p["price"]

# Ranking diário
ranking.sort(reverse=True,key=lambda x:x[0])
if ranking:
    msg="🏆 TOP OFERTAS DO DIA\n\n"
    for i,(_,p) in enumerate(ranking[:5],1):
        msg+=f"{i}️⃣ {p['name']} – R$ {p['price']}\n"
    bot.send_message(CHAT_ID,msg)

# Salva histórico
json.dump(history,open("history.json","w"))
