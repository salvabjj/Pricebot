import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO
from datetime import datetime

# Arquivos de Dados
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

def limpar_url(url):
    return url.split('?')[0].split('#')[0]

def escolher_frase_inteligente(titulo, copies):
    t = titulo.lower()
    keywords = {
        "eletronicos": ["iphone", "smartphone", "fone", "bluetooth", "smartwatch", "caixa", "som", "ps5", "nintendo", "monitor", "gamer", "tv", "notebook"],
        "fitness": ["whey", "creatina", "pre treino", "suplemento", "termogenico", "shaker", "proteina", "bcaa"],
        "esportes": ["boxe", "jiu jitsu", "muay thai", "saco", "luva", "tenis", "kimono", "bandagem", "corrida", "bicicleta"],
        "eletrodomesticos": ["fryer", "geladeira", "micro-ondas", "aspirador", "alexa", "cafeteira", "maquina", "fogão"],
        "moda": ["casual", "camisa", "vestido", "calça", "jeans", "perfume", "relogio", "maquiagem", "óculos"]
    }
    for categoria, palavras in keywords.items():
        if any(p in t for p in palavras):
            return random.choice(copies.get(categoria, copies["fallback"]))
    return random.choice(copies.get("fallback", ["🔥 Confira essa oferta:"]))

def extrair_detalhes(url, loja_nome):
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ]
    headers = {"User-Agent": random.choice(ua_list), "Referer": "https://www.google.com/"}
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        t = soup.find("h1") or soup.find("meta", property="og:title")
        nome = (t.get_text().strip() if t and not t.has_attr("content") else t["content"]) if t else "Oferta"
        nome = re.sub(r'| Mercado Livre| | Amazon| | Netshoes| | Shopee| | Zattini', '', nome, flags=re.IGNORECASE).strip()

        img_tag = soup.find("meta", property="og:image:secure_url") or soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        if not img_url: return None, None, None

        texto = res.text.replace('\n', ' ').replace('\xa0', ' ')
        precos = re.findall(r'(?:R\$|R\$\s?|Price:)\s?([\d\.]+\,\d{2})', texto)
        preco_final = f"💰 *Preço: R$ {precos[0]}*" if precos else "🔥 *Confira o valor no site!*"

        img_headers = headers.copy()
        img_headers["Referer"] = url 
        img_res = requests.get(img_url, headers=img_headers, timeout=10)
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
    report_chat_id = os.getenv("REPORT_CHAT_ID", chat_id) 
    
    history = load_json(HISTORY_FILE)
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)
    
    start_time = datetime.now()
    stats = {"enviados": 0, "lojas": {}, "erros": 0}
    
    nichos = config.get("nichos", [])
    sites = config.get("sites", [])
    random.shuffle(nichos)
    
    for nicho in nichos:
        if stats["enviados"] >= 10: break
        random.shuffle(sites)
        for site in sites:
            if stats["enviados"] >= 10: break
            termo = random.choice(nicho["termos"])
            print(f"🔎 Buscando: {termo} em {site['nome']}")
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/dp/", "/item/", "MLB-", "-P_"])]
                random.shuffle(links)
                
                for l in links[:15]:
                    url_f = limpar_url(tratar_link(l, site['nome']))
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
                            stats["enviados"] += 1
                            stats["lojas"][site['nome']] = stats["lojas"].get(site['nome'], 0) + 1
                            print(f"✅ POSTADO: {nome[:30]}")
                            time.sleep(15) 
                            break
                        except:
                            stats["erros"] += 1
                            continue
            except:
                stats["erros"] += 1
                continue

    # --- RELATÓRIO FINAL ---
    end_time = datetime.now()
    duration = end_time - start_time
    lojas_info = "\n".join([f"📍 {l}: {c}" for l, c in stats["lojas"].items()])
    
    relatorio = (
        f"📊 *RELATÓRIO DE ATIVIDADE*\n"
        f"🕒 Finalizado em: `{end_time.strftime('%H:%M:%S')}`\n"
        f"⏱ Duração: `{str(duration).split('.')[0]}`\n\n"
        f"✅ *Ofertas postadas:* {stats['enviados']}\n"
        f"⚠️ *Falhas/Bloqueios:* {stats['erros']}\n\n"
        f"🏢 *Por Loja:*\n{lojas_info if lojas_info else 'Nenhuma'}"
    )
    
    try:
        bot.send_message(report_chat_id, text=relatorio, parse_mode="Markdown")
    except:
        pass

    save_json(HISTORY_FILE, history[-600:])

if __name__ == "__main__":
    main()
