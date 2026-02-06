import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

HISTORY_FILE = "History.json"
AFFILIATES_FILE = "Affiliates.json"
CATEGORIES_FILE = "Categories.json"
COPY_FILE = "Copy.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def extrair_detalhes(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 1. Nome
        title = soup.find("meta", property="og:title") or soup.find("h1")
        nome = title["content"].split("|")[0].strip() if title and title.has_attr("content") else (title.get_text().strip() if title else "Produto")
        
        # 2. Imagem (Melhorado para Amazon e Netshoes)
        img = soup.find("meta", property="og:image") or soup.find("img", {"id": "landingImage"}) or soup.find("img", {"id": "main-photo"})
        img_url = img["content"] if img and img.has_attr("content") else (img["src"] if img and img.has_attr("src") else None)
        
        # 3. PREÇO (O grande desafio)
        preco = None
        
        # Tentativa A: Atributos de Meta (Comum em Netshoes/Zattini)
        meta_p = soup.find("meta", property="product:price:amount") or soup.find("span", {"itemprop": "price"})
        if meta_p:
            v = meta_p.get("content") or meta_p.get_text()
            if v: preco = f"💰 *Apenas: R$ {v.strip().replace('R$', '').strip()}*"

        # Tentativa B: JSON estruturado (Netshoes/Amazon)
        if not preco:
            scripts = soup.find_all("script", type="application/ld+json")
            for s in scripts:
                try:
                    data = json.loads(s.string)
                    if isinstance(data, list): data = data[0]
                    main_offer = data.get("offers", {})
                    if isinstance(main_offer, list): main_offer = main_offer[0]
                    p = main_offer.get("price")
                    if p: 
                        preco = f"💰 *Apenas: R$ {str(p).replace('.', ',')}*"
                        break
                except: continue

        # Tentativa C: Seletores de texto (Amazon/ML)
        if not preco:
            for selector in [".a-offscreen", ".price-tag-fraction", ".default-price"]:
                tag = soup.select_one(selector)
                if tag:
                    preco = f"💰 *Apenas: {tag.get_text().strip()}*"
                    break

        if not preco:
            preco = "🔥 *VALOR PROMOCIONAL NO SITE!*"
            
        return nome, img_url, preco
    except: return None, None, None

def converter_afiliado(url, site_nome, ids):
    s = site_nome.lower()
    if "amazon" in s: return f"{url}&tag={ids.get('amazon', 'salvablessjj-20')}" if "?" in url else f"{url}?tag={ids.get('amazon', 'salvablessjj-20')}"
    if "shopee" in s: return f"https://shopee.com.br/universal-link/{ids.get('shopee', '18308930971')}?url={url}"
    if "mercadolivre" in s: return f"{url}#id={ids.get('mercadolivre', '1561730990')}"
    if "netshoes" in s or "zattini" in s: return f"{url}?campaign={ids.get('netshoes', 'rWODdSNWJGM')}"
    return url

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)

    enviados_total = 0
    meta = 3
    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if enviados_total >= meta: break
        sites = config.get("sites", [])
        random.shuffle(sites)

        for site in sites:
            if enviados_total >= meta: break
            termo = random.choice(nicho["termos"])
            print(f"Buscando {termo} em {site['nome']}...")
            
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if any(x in href for x in ["/p/", "/item/", "/dp/", "produto.mercadolivre"]):
                        if not href.startswith("http"):
                            base = "https://www.mercadolivre.com.br" if "mercadolivre" in site['nome'].lower() else f"https://www.{site['nome'].lower()}.com.br"
                            href = base + (href if href.startswith("/") else "/" + href)
                        links.append(href)
                random.shuffle(links)
            except: links = []

            for link in links:
                if link not in history:
                    nome, img, texto_venda = extrair_detalhes(link)
                    if not nome or len(nome) < 15: continue 

                    link_af = converter_afiliado(link, site["nome"], afiliados)
                    frase_topo = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                    
                    msg = f"{frase_topo}\n\n📦 *{nome[:85]}...*\n\n{texto_venda}\n\n🛒 Loja: {site['nome'].upper()}"
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 VER PREÇO E COMPRAR", url=link_af)]])

                    try:
                        if img: bot.send_photo(chat_id=chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                        else: bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(link)
                        enviados_total += 1
                        print(f"✅ Sucesso {enviados_total}/3")
                        time.sleep(10)
                        break 
                    except: continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-500:], f, indent=2)

if __name__ == "__main__":
    main()
