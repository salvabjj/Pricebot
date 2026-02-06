import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot
from io import BytesIO

# --- NICHOS DEFINIDOS ---
TERMOS_ML = ["quimono jiu jitsu", "whey protein", "creatina", "perfume masculino"]
# Termos focados em Casa/Choice para Shopee
TERMOS_SHOPEE = ["organizador casa", "shopee choice", "utensilios cozinha", "decoração sala"]

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.google.com/"
    }

def extrair_detalhes_ml(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.text, "html.parser")
        
        nome = soup.find("h1").get_text().strip() if soup.find("h1") else "Oferta"
        img = soup.find("meta", property="og:image")["content"]
        
        # Pega o preço no texto (mais estável que seletor CSS)
        precos = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', res.text)
        preco = f"R$ {precos[0]}" if precos else "Confira"
        
        return {"nome": nome[:90], "img": img, "preco": preco, "url": url}
    except: return None

def buscar_shopee_api(termo):
    # A Shopee bloqueia o HTML, mas a API de busca às vezes permite o acesso
    url = f"https://shopee.com.br/api/v4/search/search_items?keyword={termo}&limit=5&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH"
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        data = res.json()
        items = data.get('items', [])
        if not items: return []
        
        results = []
        for i in items:
            item = i.get('item_basic')
            if item:
                # Monta link e imagem manualmente
                link = f"https://shopee.com.br/product/{item['shopid']}/{item['itemid']}"
                img = f"https://down-br.img.sgrid.id/file/{item['image']}"
                preco = f"R$ {item['price']/100000:.2f}".replace('.', ',')
                results.append({"nome": item['name'], "img": img, "preco": preco, "url": link})
        return results
    except: return []

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    history = [] # Carregue seu History.json aqui
    
    # 1. TENTATIVA MERCADO LIVRE
    print("🔎 Buscando no Mercado Livre...")
    termo = random.choice(TERMOS_ML)
    res_ml = requests.get(f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}", headers=get_headers())
    links_ml = re.findall(r'https://produto\.mercadolivre\.com\.br/MLB-\d+-[^"\'\s]+', res_ml.text)
    
    for link in list(set(links_ml))[:3]:
        if link in history: continue
        prod = extrair_detalhes_ml(link)
        if prod:
            bot.send_photo(chat_id, photo=prod['img'], caption=f"💎 *MERCADO LIVRE*\n\n📦 {prod['nome']}\n💰 *{prod['preco']}*\n\n🛒 [COMPRAR]({prod['url']})", parse_mode="Markdown")
            print(f"✅ Postado ML: {prod['nome']}")
            return # Para após postar uma para evitar spam

    # 2. TENTATIVA SHOPEE (API)
    print("🔎 Buscando na Shopee...")
    produtos_sh = buscar_shopee_api(random.choice(TERMOS_SHOPEE))
    for prod in produtos_sh:
        if prod['url'] in history: continue
        bot.send_photo(chat_id, photo=prod['img'], caption=f"🏠 *SHOPEE CASA*\n\n📦 {prod['nome']}\n💰 *{prod['preco']}*\n\n🛒 [COMPRAR]({prod['url']})", parse_mode="Markdown")
        print(f"✅ Postado Shopee: {prod['nome']}")
        break

if __name__ == "__main__":
    main()
