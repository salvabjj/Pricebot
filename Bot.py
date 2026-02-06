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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        title_tag = soup.find("meta", property="og:title") or soup.find("h1")
        nome = title_tag["content"] if title_tag and title_tag.has_attr("content") else (title_tag.get_text().strip() if title_tag else "Produto")
        nome = nome.split('|')[0].split('-')[0].strip()
        img_tag = soup.find("meta", property="og:image") or soup.find("img")
        img_url = img_tag["content"] if img_tag and img_tag.has_attr("content") else (img_tag["src"] if img_tag and img_tag.has_attr("src") else None)
        
        preco = None
        script_json = soup.find("script", type="application/ld+json")
        if script_json:
            try:
                data = json.loads(script_json.string)
                if isinstance(data, list): data = data[0]
                p = data.get("offers", {}).get("price") or data.get("offers", [{}])[0].get("price")
                if p: preco = f"💰 *R$ {str(p).replace('.', ',')}*"
            except: pass
        if not preco:
            texto_sem_parcela = re.sub(r'\d+\s?[xX]\s?de\s?R\$\s?[\d.,]+', '', res.text)
            match = re.search(r'R\$\s?(\d{1,3}(\.\d{3})*,\d{2})', texto_sem_parcela)
            preco = f"💰 *{match.group(0)}*" if match else "🔥 *VEJA NO SITE!*"
        return nome, img_url, preco
    except: return None, None, None

def converter_afiliado(url, site_nome, ids):
    s = site_nome.lower()
    if "amazon" in s: return f"{url}&tag={ids.get('amazon', 'salvablessjj-20')}"
    if "shopee" in s: return f"https://shopee.com.br/universal-link/{ids.get('shopee', '18308930971')}?url={url}"
    if "mercadolivre" in s: return f"{url}#id={ids.get('mercadolivre', '1561730990')}"
    if "netshoes" in s: return f"{url}?campaign={ids.get('netshoes', 'rWODdSNWJGM')}"
    return url

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)

    postados = [] # Lista de nomes de lojas postadas nesta execução
    total_enviados = 0
    max_posts = 10
    
    # Ordem de prioridade para o ML
    termos_ml_preferencial = ["geladeira", "iphone", "smart tv", "suplemento whey", "creatina", "air fryer"]

    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if total_enviados >= max_posts: break
        
        sites = config.get("sites", [])
        # Embaralha, mas se o último foi ML, prioriza Shopee. Se foi Netshoes, prioriza Amazon.
        if postados:
            ultimo = postados[-1].lower()
            if "mercadolivre" in ultimo:
                sites.sort(key=lambda x: "shopee" not in x["nome"].lower())
            elif "netshoes" in ultimo:
                sites.sort(key=lambda x: "amazon" not in x["nome"].lower())

        for site in sites:
            if total_enviados >= max_posts: break
            
            # Preferência de termos para o ML
            if "mercadolivre" in site['nome'].lower():
                termo = random.choice(termos_ml_preferencial)
            else:
                termo = random.choice(nicho["termos"])

            print(f"Tentando: {termo} na {site['nome']}")
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/dp/", "/item/", "produto"])]
                
                for link in links:
                    if total_enviados >= max_posts: break
                    if not link.startswith("http"):
                        base = "https://www.netshoes.com.br" if "netshoes" in site['nome'].lower() else "https://www.mercadolivre.com.br"
                        link = base + ("" if link.startswith("/") else "/") + link

                    if link not in history:
                        nome, img, preco = extrair_detalhes(link)
                        if not nome or len(nome) < 5 or "Netshoes" in nome: continue

                        link_af = converter_afiliado(link, site["nome"], afiliados)
                        msg = f"🔥 {random.choice(copies.get(nicho['id'], ['OFERTA!']))}\n\n📦 *{nome[:95]}*\n\n{preco}\n\n🛒 Loja: {site['nome'].upper()}"
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR AGORA", url=link_af)]])

                        if img: bot.send_photo(chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                        else: bot.send_message(chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(link)
                        postados.append(site['nome'])
                        total_enviados += 1
                        print(f"✅ Enviado {total_enviados}: {site['nome']}")
                        time.sleep(10)
                        break 
            except: continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-500:], f, indent=2)

if __name__ == "__main__":
    main()
