import requests, json, os, random
from bs4 import BeautifulSoup
import telegram

# -----------------------------
# Configurações do Telegram
# -----------------------------
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", 0))  # garante que seja inteiro

bot = telegram.Bot(token=TOKEN)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# -----------------------------
# Função para carregar arquivos JSON
# -----------------------------
def load(file, default):
    return json.load(open(file)) if os.path.exists(file) else default

# -----------------------------
# Carregar arquivos
# -----------------------------
categories = load("categories.json", [])
history = load("history.json", {})
copies = load("copy.json", {})
affiliates = load("affiliates.json", {})

ranking = []
total_found = 0

# -----------------------------
# Função para aplicar link afiliado
# -----------------------------
def apply_affiliate(url, niche):
    if "amazon" in url: return affiliates.get("amazon", url)
    if "shopee" in url: return affiliates.get("shopee", url)
    if "mercadolivre" in url: return affiliates.get("mercadolivre", url)
    if "netshoes" in url: return affiliates.get("netshoes", url)
    return url

# -----------------------------
# Função para pegar cupom (opcional)
# -----------------------------
def get_coupon(niche):
    try:
        with open(f"coupons_{niche}.json","r") as f:
            cupons = json.load(f)
            return random.choice(cupons) if cupons else ""
    except:
        return ""

# -----------------------------
# Função para pegar produtos
# -----------------------------
def get_products(url):
    try:
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
    except Exception as e:
        print(f"[ERRO] Falha ao buscar produtos de {url}: {e}")
        return []

# -----------------------------
# Loop principal
# -----------------------------
for cat in categories:
    products = get_products(cat["search_url"])
    total_found += len(products)
    print(f"[INFO] Categoria '{cat['category']}' - {len(products)} produtos encontrados")

    for p in products:
        key = p["name"]
        old_price = history.get(key, p["price"])
        discount = round((old_price - p["price"]) / old_price * 100, 1) if old_price else 0
        score = discount*2 + (old_price - p["price"])

        # Posta mesmo sem cupom, mínimo 5% de desconto
        if discount >= 5:
            text = random.choice(copies.get(cat["niche"], ["🔥 OFERTA!\n👉 Veja:"]))
            link = apply_affiliate(p["url"], cat["niche"])
            cupom = get_coupon(cat["niche"])
            cupom_text = f"\n🎫 Use o cupom: {cupom}" if cupom else ""
            msg = f"{text}\n{p['name']}\n💰 R$ {p['price']} (-{discount}%)\n{link}{cupom_text}"
            
            # Tenta enviar mensagem e registra log
            try:
                bot.send_message(CHAT_ID, msg)
                print(f"[INFO] Mensagem enviada: {p['name'][:50]}...")
            except Exception as e:
                print(f"[ERRO] Não foi possível enviar a mensagem: {e}")

            ranking.append((score,p))

        # Atualiza histórico
        history[key] = p["price"]

# -----------------------------
# Ranking diário
# -----------------------------
ranking.sort(reverse=True,key=lambda x:x[0])
if ranking:
    msg="🏆 TOP OFERTAS DO DIA\n\n"
    for i,(_,p) in enumerate(ranking[:5],1):
        msg+=f"{i}️⃣ {p['name']} – R$ {p['price']}\n"
    try:
        bot.send_message(CHAT_ID,msg)
        print("[INFO] Ranking diário enviado")
    except Exception as e:
        print(f"[ERRO] Não foi possível enviar o ranking: {e}")

# -----------------------------
# Log total produtos encontrados
# -----------------------------
print(f"[INFO] Total de produtos encontrados nesta execução: {total_found}")

# -----------------------------
# Salva histórico
# -----------------------------
json.dump(history, open("history.json","w"))
