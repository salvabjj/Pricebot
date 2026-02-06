import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO

# Arquivos
HISTORY_FILE = "History.json"
AFFILIATES_FILE = "Affiliates.json"
CATEGORIES_FILE = "Categories.json"
COPY_FILE = "Copy.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return [] if "History" in file else {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def escolher_frase_inteligente(titulo, copies):
    t = titulo.lower()
    keywords = {
        "eletronicos": ["iphone", "smartphone", "fone", "bluetooth", "smartwatch", "caixa", "som", "ps5", "nintendo", "monitor", "gamer", "tv", "eletro"],
        "fitness": ["whey", "creatina", "pre treino", "suplemento", "termogenico", "shaker", "proteina"],
        "esportes": ["boxe", "jiu jitsu", "muay thai", "saco", "luva", "tenis", "kimono", "bandagem", "corrida", "pancada"],
        "eletrodomesticos": ["fryer", "geladeira", "micro-ondas", "aspirador", "alexa", "cafeteira", "maquina", "cozinha"],
        "moda": ["casual", "camisa", "vestido", "calça", "jeans", "perfume", "relogio", "maquiagem", "look", "outlet"]
    }
    
    for categoria, palavras in keywords.items():
        if any(p in t for p in palavras):
            return random.choice(copies.get(categoria, copies["fallback"]))
    return random.choice(copies.get("fallback", ["🔥 Confira esta oferta!"]))

def extrair_detalhes(url, loja_nome):
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    headers = {"User-Agent": random.choice(ua_list), "Referer": "https://www.google.com/"}

    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        t = soup.find("h1") or soup.find("meta", property="og:title")
        nome = (t.get_text().strip() if t and not t.has_attr("content") else t["content"]) if t else "Oferta Especial"
        nome = re.sub(r'| Mercado Livre| | Amazon| | Netshoes| | Shopee| | Zattini', '', nome, flags=re.IGNORECASE).strip()

        img_tag = soup.find("meta", property="og:image") or soup.find("meta", name="twitter:image")
        img_url = img_tag["content"] if img_tag else None
        if not img_url: return None, None, None

        precos = re.findall(r'R\$\s?[\d\.]+\,\d{2}', res.text.replace('\n', ' '))
        preco_final = f"💰 *Preço: {precos[0]}*" if precos else "🔥 *Confira o preço no site!*"

        # TENTATIVA DUPLA DE DOWNLOAD (Mais persistência)
        img_headers = headers.copy()
        img_headers["Referer"] = url 
        img_res = requests.get(img_url, headers=img_headers, timeout=10)
        
        if img_res.status_code != 200: # Se falhar, tenta sem referer (alguns CDNs preferem assim)
            img_res = requests.get(img_url, headers={"User-Agent": random.choice(ua_list)}, timeout=10)

        if img_res.status_code == 200:
            return nome[:100], BytesIO(img_res.content), preco_final
        return None, None, None
    except: return None, None, None

def tratar_link(link, loja_nome):
    if link.startswith("http"): return link
    bases = {"mercadolivre": "https://www.mercadolivre.com.br", "netshoes": "https://www.netshoes.com.br", 
             "shopee": "https://shopee.com.br", "amazon": "https://www.amazon.com.br", "zattini": "https://www.zattini.com.br"}
    for k, v in bases.items():
        if k in loja_nome.lower().replace(" ", ""): return v + ("" if link.startswith("/") else "/") + link
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
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)
    
    total_enviados = 0
    nichos = config.get("nichos", [])
    sites = config.get("sites", [])
    random.shuffle(nichos)
    
    for nicho in nichos:
        if total_enviados >= 10: break
        random.shuffle(sites)
        for site in sites:
            if total_enviados >= 10: break
            termo = random.choice(nicho["termos"])
            print(f"🔎 Buscando: {termo} em {site['nome']}")
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/dp/", "/item/", "MLB-", "-P_"])]
                random.shuffle(links)
                
                for l in links[:12]:
                    url_f = tratar_link(l, site['nome'])
                    if url_f in history: continue
                    
                    nome, foto_bytes, valor = extrair_detalhes(url_f, site['nome'])
                    
                    if nome and foto_bytes:
                        url_af = converter_afiliado(url_f, site['nome'], afiliados)
                        frase = escolher_frase_inteligente(nome, copies)
                        
                        msg = f"{frase}\n\n📦 *{nome}*\n\n{valor}\n\n🛒 Loja: {site['nome'].upper()}"
                        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR AGORA", url=url_af)]])
                        
                        try:
                            bot.send_photo(chat_id, photo=foto_bytes, caption=msg, reply_markup=btn, parse_mode="Markdown")
                            history.append(url_f)
                            total_enviados += 1
                            print(f"✅ SUCESSO: {nome[:30]}")
                            time.sleep(15) # Intervalo anti-spam
                            break
                        except Exception as e:
                            print(f"Erro Telegram: {e}")
                            continue
            except: continue
    save_json(HISTORY_FILE, history[-500:])

if __name__ == "__main__":
    main()
    
