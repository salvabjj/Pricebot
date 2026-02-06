import os, json, random, time, requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# CONFIGURAÇÃO DE ARQUIVOS
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        img = soup.find("meta", property="og:image")
        img_url = img["content"] if img else None
        title = soup.find("meta", property="og:title")
        nome = title["content"].split("|")[0].strip() if title else "Produto em Oferta"
        
        preco = None
        for tag in soup.find_all(["span", "strong", "p"]):
            texto = tag.get_text().strip()
            if "R$" in texto and len(texto) < 15:
                preco = f"💰 *Apenas: {texto}*"
                break
        
        if not preco:
            preco = random.choice(["🔥 *O PREÇO CAIU!* (Veja no botão)", "😱 *OFERTA EXCLUSIVA!*", "📉 *MENOR PREÇO DO MÊS!*"])
            
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
    lojas_usadas = [] # Lista para evitar repetir a mesma loja 3 vezes seguidas
    
    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if enviados_total >= 3: break

        # SORTEIO DE LOJAS: Prioriza sites diferentes
        sites = config.get("sites", [])
        random.shuffle(sites)

        for site in sites:
            if enviados_total >= 3: break
            
            # Tenta evitar repetir a loja da mensagem anterior se possível
            if site["nome"] in lojas_usadas and len(lojas_usadas) < len(sites):
                continue

            termo = random.choice(nicho["termos"])
            # Filtro para nicho Choice (Exclusivo Shopee)
            if nicho["id"] == "choice" and "shopee" not in site["nome"]: continue
            
            print(f"Buscando {termo} em {site['nome']}...")
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers=headers, timeout=12)
                soup = BeautifulSoup(r.text, "html.parser")
                # Busca links específicos por loja
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/item/", "/dp/"])]
            except: links = []

            for link in list(set(links)):
                if not link.startswith("http"):
                    link = f"https://www.{site['nome'].lower()}.com.br" + (link if link.startswith("/") else "/" + link)

                if link not in history:
                    nome, img, texto_venda = extrair_detalhes(link)
                    if not nome or "Amazon" in nome and len(nome) < 10: continue 

                    link_af = converter_afiliado(link, site["nome"], afiliados)
                    frase_topo = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                    
                    msg = f"{frase_topo}\n\n📦 *{nome[:80]}...*\n\n{texto_venda}\n\n🛒 Loja: {site['nome'].upper()}"
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 VER PREÇO E COMPRAR", url=link_af)]])

                    try:
                        if img: bot.send_photo(chat_id=chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                        else: bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(link)
                        lojas_usadas.append(site["nome"])
                        enviados_total += 1
                        time.sleep(15)
                        break 
                    except: continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-500:], f, indent=2)

if __name__ == "__main__":
    main()
