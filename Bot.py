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
        loja = loja_nome.lower()
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 1. Extrai o Título Real do Produto
        t = soup.find("h1") or soup.find("meta", property="og:title")
        nome = (t.get_text().strip() if t and not t.has_attr("content") else t["content"]) if t else "Produto Especial"
        
        # 2. DETECTOR DE BLOQUEIO (Amazon e ML)
        # Se o título tiver palavras de erro ou login, cancelamos o print
        bloqueio_termos = ["login", "signin", "captcha", "robot", "verificação", "acesso negado"]
        foi_bloqueado = any(termo in nome.lower() or termo in res.url.lower() for termo in bloqueio_termos)

        # Limpa o nome das lojas
        nome = re.sub(r'| Mercado Livre| | Amazon| | Netshoes| | Shopee', '', nome, flags=re.IGNORECASE).strip()

        # 3. Define se usa PRINT ou FOTO LIMPA
        usar_print = ("amazon" in loja or "mercadolivre" in loja) and not foi_bloqueado
        
        if usar_print:
            print(f"📸 Gerando print para {loja_nome}...")
            img = f"https://s0.wp.com/mshots/v1/{url}?w=1024&h=768"
            preco = "✅ *Preço no print da tela acima!*"
            return nome[:100], img, preco

        # 4. LÓGICA DE FOTO LIMPA (Backup para bloqueios ou outras lojas)
        print(f"🖼️ Usando foto limpa para {loja_nome} (Bloqueio ou Loja Padrão).")
        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag else None
        
        # Tenta pegar o preço no texto
        texto_limpo = re.sub(r'\d+\s?[xX]\s?de\s?R\$\s?[\d.,]+', '', res.text)
        match = re.search(r'R\$\s?(\d{1,3}(\.\d{3})*,\d{2})', texto_limpo)
        preco = f"💰 *Apenas: {match.group(0)}*" if match else "🔥 *Confira o preço no site!*"
            
        return nome[:100], img, preco
    except Exception as e:
        print(f"Erro na extração: {e}")
        return None, None, None

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
    
    total_enviados = 0
    lojas_nesta_rodada = []
    sites = config.get("sites", [])
    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if total_enviados >= 10: break
        random.shuffle(sites)
        for site in sites:
            if total_enviados >= 10: break
            if lojas_nesta_rodada and lojas_nesta_rodada[-1] == site['nome']: continue

            termo = random.choice(nicho["termos"])
            print(f"🔎 Buscando: {termo} em {site['nome']}")
            
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/dp/", "/item/", "MLB-", "-P_"])]
                
                for l in random.sample(links, min(len(links), 8)):
                    url_real = tratar_link(l, site['nome'])
                    if url_real in history: continue
                    
                    nome, img, preco = extrair_detalhes(url_real, site['nome'])
                    
                    if nome and img:
                        url_af = converter_afiliado(url_real, site['nome'], afiliados)
                        msg = f"{random.choice(copies.get(nicho['id'], ['🔥 OFERTA!']))}\n\n📦 *{nome}*\n\n{preco}\n\n🛒 Loja: {site['nome'].upper()}"
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR AGORA", url=url_af)]])

                        try:
                            bot.send_photo(chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                            history.append(url_real)
                            lojas_nesta_rodada.append(site['nome'])
                            total_enviados += 1
                            print(f"✅ Enviado: {site['nome']} ({total_enviados}/10)")
                            time.sleep(12)
                            break
                        except: continue
            except: continue

    save_json(HISTORY_FILE, history[-500:])
    save_json(LAST_STORE_FILE, {"last_store": lojas_nesta_rodada[-1] if lojas_nesta_rodada else ""})

if __name__ == "__main__":
    main()
