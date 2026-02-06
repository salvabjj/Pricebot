import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Arquivos de Dados
HISTORY_FILE = "History.json"
AFFILIATES_FILE = "Affiliates.json"
CATEGORIES_FILE = "Categories.json"
COPY_FILE = "Copy.json"
LAST_STORE_FILE = "LastStore.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extrair_detalhes(url, loja_nome):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    try:
        is_amazon = "amazon" in loja_nome.lower()
        
        # TELA INTEIRA PARA AMAZON (Via mshots para evitar bloqueio 403)
        if is_amazon:
            img = f"https://s0.wp.com/mshots/v1/{url}?w=1024&h=768"
            nome = "Oferta Especial Amazon"
            preco = "✅ *Preço no print da tela acima!*"
            # Tenta pegar o nome real apenas para a legenda
            try:
                r_amz = requests.get(url, headers=headers, timeout=10)
                s_amz = BeautifulSoup(r_amz.text, "html.parser")
                t = s_amz.find("h1", id="title") or s_amz.find("meta", property="og:title")
                if t: nome = t.get_text().strip()[:100]
            except: pass
            return nome, img, preco

        # LÓGICA NORMAL PARA OUTRAS LOJAS
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        title = soup.find("meta", property="og:title") or soup.find("h1")
        nome = title["content"] if title and title.has_attr("content") else (title.get_text().strip() if title else "Produto")
        nome = re.sub(r'| Netshoes| | Mercado Livre| | Shopee| | Zattini', '', nome, flags=re.IGNORECASE).strip()

        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag else None

        texto_limpo = re.sub(r'\d+\s?[xX]\s?de\s?R\$\s?[\d.,]+', '', res.text)
        match = re.search(r'R\$\s?(\d{1,3}(\.\d{3})*,\d{2})', texto_limpo)
        preco = f"💰 *Apenas: {match.group(0)}*" if match else "🔥 *Confira o preço no site!*"
            
        return nome, img, preco
    except: return None, None, None

def tratar_link(link, loja_nome):
    if link.startswith("http"): return link
    bases = {"mercadolivre": "https://www.mercadolivre.com.br", "netshoes": "https://www.netshoes.com.br", 
             "zattini": "https://www.zattini.com.br", "shopee": "https://shopee.com.br", "amazon": "https://www.amazon.com.br"}
    for chave, base in bases.items():
        if chave in loja_nome.lower(): return base + ("" if link.startswith("/") else "/") + link
    return link

def converter_afiliado(url, site_nome, ids):
    s = site_nome.lower()
    if "amazon" in s: return f"{url}?tag={ids.get('amazon', 'salvablessjj-20')}"
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
    memoria = load_json(LAST_STORE_FILE)
    
    ultima_loja_global = memoria.get("last_store", "")
    total_enviados = 0
    max_posts = 10
    lojas_nesta_rodada = []
    
    ordem_sites = list(config.get("sites", []))
    if ultima_loja_global:
        if "mercadolivre" in ultima_loja_global.lower():
            ordem_sites.sort(key=lambda x: "shopee" not in x["nome"].lower())
        elif "netshoes" in ultima_loja_global.lower():
            ordem_sites.sort(key=lambda x: "amazon" not in x["nome"].lower())

    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if total_enviados >= max_posts: break
        for site in ordem_sites:
            if total_enviados >= max_posts: break
            
            # Regra de Pares
            if lojas_nesta_rodada:
                anterior = lojas_nesta_rodada[-1].lower()
                if "mercadolivre" in anterior and "shopee" not in site['nome'].lower(): continue
                if "netshoes" in anterior and "amazon" not in site['nome'].lower(): continue

            termo = random.choice(nicho["termos"])
            print(f"🔎 Buscando: {termo} em {site['nome']}")
            
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/dp/", "/item/", "MLB-"])]
                random.shuffle(links)

                for l in links:
                    url_real = tratar_link(l, site['nome'])
                    if url_real in history: continue
                    
                    nome, img, preco = extrair_detalhes(url_real, site['nome'])
                    
                    if nome and img:
                        url_af = converter_afiliado(url_real, site['nome'], afiliados)
                        frase = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                        msg = f"{frase}\n\n📦 *{nome}*\n\n{preco}\n\n🛒 Loja: {site['nome'].upper()}"
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR AGORA", url=url_af)]])

                        try:
                            bot.send_photo(chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                            history.append(url_real)
                            lojas_nesta_rodada.append(site['nome'])
                            ultima_loja_global = site['nome']
                            total_enviados += 1
                            print(f"✅ Enviado: {site['nome']} ({total_enviados}/10)")
                            time.sleep(15)
                            break
                        except Exception as e:
                            print(f"Erro Telegram: {e}")
                            continue
            except: continue

    save_json(HISTORY_FILE, history[-500:])
    save_json(LAST_STORE_FILE, {"last_store": ultima_loja_global})

if __name__ == "__main__":
    main()
