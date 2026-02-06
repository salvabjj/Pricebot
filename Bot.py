import os, json, random, time, requests
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Nome do Produto
        title = soup.find("meta", property="og:title") or soup.find("h1")
        nome = title["content"].split("|")[0].strip() if title and title.has_attr("content") else (title.get_text().strip() if title else "Produto em Oferta")
        
        # Imagem (Amazon, ML e outros)
        img = soup.find("meta", property="og:image") or soup.find("img", {"id": "landingImage"})
        img_url = img["content"] if img and img.has_attr("content") else (img["src"] if img and img.has_attr("src") else None)
        
        # Busca de Preço (Melhorada para Netshoes e ML)
        preco = None
        # Tenta seletor de preço padrão de e-commerce
        meta_preco = soup.find("meta", property="product:price:amount") or soup.find("span", {"itemprop": "price"})
        if meta_preco:
            valor = meta_preco.get("content") or meta_preco.get_text()
            preco = f"💰 *Apenas: R$ {valor.strip()}*"
        
        # Se não achou meta, tenta busca textual
        if not preco:
            for tag in soup.find_all(["span", "strong", "p"]):
                txt = tag.get_text().strip()
                if "R$" in txt and len(txt) < 20:
                    preco = f"💰 *Apenas: {txt}*"
                    break
        
        # Frase de impacto se o preço falhar
        if not preco:
            preco = random.choice(["🔥 *PREÇO IMBATÍVEL!*", "😱 *DESCONTO ATIVO!*", "📉 *BAIXOU O PREÇO!*"])
            
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
    lojas_na_rodada = [] 

    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if enviados_total >= meta: break
        sites = config.get("sites", [])
        random.shuffle(sites)

        for site in sites:
            if enviados_total >= meta: break
            if site["nome"] in lojas_na_rodada and len(lojas_na_rodada) < len(sites): continue

            termo = random.choice(nicho["termos"])
            print(f"Buscando {termo} em {site['nome']}...")
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/item/", "/dp/", "produto.mercadolivre"])]
                random.shuffle(links)
            except Exception as e:
                print(f"Erro ao buscar no site {site['nome']}: {e}")
                links = []

            for link in links:
                if not link.startswith("http"):
                    link = f"https://www.{site['nome'].lower()}.com.br" + (link if link.startswith("/") else "/" + link)

                if link not in history:
                    nome, img, texto_venda = extrair_detalhes(link)
                    if not nome or len(nome) < 10: continue 

                    link_af = converter_afiliado(link, site["nome"], afiliados)
                    frase_topo = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                    
                    msg = f"{frase_topo}\n\n📦 *{nome[:85]}...*\n\n{texto_venda}\n\n🛒 Loja: {site['nome'].upper()}"
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 VER PREÇO E COMPRAR", url=link_af)]])

                    try:
                        if img: bot.send_photo(chat_id=chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                        else: bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(link)
                        lojas_na_rodada.append(site["nome"])
                        enviados_total += 1
                        time.sleep(15)
                        break 
                    except: continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-500:], f, indent=2)

if __name__ == "__main__":
    main()
