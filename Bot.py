import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Arquivos de dados
HISTORY_FILE = "History.json"
AFFILIATES_FILE = "Affiliates.json"
CATEGORIES_FILE = "Categories.json"
COPY_FILE = "Copy.json"
LAST_STORE_FILE = "LastStore.json" # Novo arquivo para memória entre fluxos

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extrair_detalhes(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Nome e Imagem
        title = soup.find("meta", property="og:title") or soup.find("h1")
        nome = title["content"] if title and title.has_attr("content") else (title.get_text().strip() if title else "Produto")
        nome = re.sub(r'| Netshoes| | Mercado Livre| | Shopee| | Zattini', '', nome, flags=re.IGNORECASE).strip()

        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag else None
        
        # Preço Blindado
        texto_limpo = re.sub(r'\d+\s?[xX]\s?de\s?R\$\s?[\d.,]+', '', res.text)
        match = re.search(r'R\$\s?(\d{1,3}(\.\d{3})*,\d{2})', texto_limpo)
        preco = f"💰 *Apenas: {match.group(0)}*" if match else "🔥 *Veja o preço no site!*"
            
        return nome, img, preco
    except: return None, None, None

def tratar_link(link, loja_nome):
    if link.startswith("http"): return link
    bases = {"mercadolivre": "https://www.mercadolivre.com.br", "netshoes": "https://www.netshoes.com.br", 
             "zattini": "https://www.zattini.com.br", "shopee": "https://shopee.com.br", "amazon": "https://www.amazon.com.br"}
    for chave, base in bases.items():
        if chave in loja_nome.lower(): return base + ("" if link.startswith("/") else "/") + link
    return link

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    
    # Carregar dados
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)
    memoria = load_json(LAST_STORE_FILE)
    
    ultima_loja_global = memoria.get("last_store", "") # Lê o que o bot postou na ÚLTIMA execução
    
    total_enviados = 0
    max_posts = 10
    lojas_nesta_rodada = []

    sites = config.get("sites", [])
    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    # Lógica de Início por Par (Memória Inter-Fluxo)
    ordem_sites = list(sites)
    if ultima_loja_global:
        if "mercadolivre" in ultima_loja_global.lower():
            # Se a última foi ML, coloca Shopee no topo da lista desta rodada
            ordem_sites.sort(key=lambda x: "shopee" not in x["nome"].lower())
        elif "netshoes" in ultima_loja_global.lower():
            # Se a última foi Netshoes, coloca Amazon no topo
            ordem_sites.sort(key=lambda x: "amazon" not in x["nome"].lower())

    for nicho in nichos:
        if total_enviados >= max_posts: break
        
        # Dentro da rodada, continua respeitando a alternância
        for site in ordem_sites:
            if total_enviados >= max_posts: break
            
            # Se já postou algo nesta rodada, verifica o par interno
            if lojas_nesta_rodada:
                anterior = lojas_nesta_rodada[-1].lower()
                if "mercadolivre" in anterior and "shopee" not in site['nome'].lower(): continue
                if "netshoes" in anterior and "amazon" not in site['nome'].lower(): continue

            # Termos preferenciais ML
            termo = random.choice(nicho["termos"])
            if "mercadolivre" in site['nome'].lower():
                termo = random.choice(["geladeira", "iphone", "creatina", "whey protein", "smart tv", "notebook"])

            print(f"Buscando: {termo} em {site['nome']}")
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/dp/", "/item/", "MLB-"])]
                random.shuffle(links)

                for l in links:
                    url_real = tratar_link(l, site['nome'])
                    if url_real in history: continue
                    
                    nome, img, preco = extrair_detalhes(url_real)
                    if not nome or len(nome) < 15: continue

                    # Monta link de afiliado e envia
                    # (Aqui entra sua lógica de afiliado já existente)
                    msg = f"🔥 {random.choice(copies.get(nicho['id'], ['OFERTA!']))}\n\n📦 *{nome[:100]}*\n\n{preco}\n\n🛒 Loja: {site['nome'].upper()}"
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR AGORA", url=url_real)]])

                    try:
                        if img: bot.send_photo(chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                        else: bot.send_message(chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(url_real)
                        lojas_nesta_rodada.append(site['nome'])
                        ultima_loja_global = site['nome'] # Atualiza a memória
                        total_enviados += 1
                        print(f"✅ Enviado: {site['nome']} ({total_enviados}/10)")
                        time.sleep(12)
                        break
                    except: continue
            except: continue

    # Salva o histórico e a memória para a PRÓXIMA execução
    save_json(HISTORY_FILE, history[-500:])
    save_json(LAST_STORE_FILE, {"last_store": ultima_loja_global})

if __name__ == "__main__":
    main()
