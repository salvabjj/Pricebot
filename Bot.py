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
        "Accept-Language": "pt-BR,pt;q=0.9"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 1. Nome
        title_tag = soup.find("meta", property="og:title") or soup.find("h1")
        nome = title_tag["content"] if title_tag and title_tag.has_attr("content") else (title_tag.get_text().strip() if title_tag else "")
        nome = nome.split('|')[0].split('-')[0].strip()

        # 2. Imagem
        img_tag = soup.find("meta", property="og:image") or soup.find("img", {"id": "landingImage"})
        img_url = img_tag["content"] if img_tag and img_tag.has_attr("content") else (img_tag["src"] if img_tag and img_tag.has_attr("src") else None)
        
        # 3. PREÇO (Lógica aprimorada para evitar erro em TVs e parcelas)
        preco = None
        
        # Prioridade 1: Metatags (Geralmente o preço real de venda)
        meta_p = soup.find("meta", property="product:price:amount") or soup.find("meta", property="og:price:amount")
        if meta_p:
            valor = meta_p["content"].replace(',', '.')
            preco = f"💰 *Apenas: R$ {valor.replace('.', ',')}*"

        # Prioridade 2: JSON estruturado (Muito bom para TVs/Eletrônicos)
        if not preco:
            script_json = soup.find("script", type="application/ld+json")
            if script_json:
                try:
                    data = json.loads(script_json.string)
                    if isinstance(data, list): data = data[0]
                    p = data.get("offers", {}).get("price") if isinstance(data.get("offers"), dict) else data.get("offers", [{}])[0].get("price")
                    if p: preco = f"💰 *Apenas: R$ {str(p).replace('.', ',')}*"
                except: pass

        # Prioridade 3: Busca por R$ no texto (Filtra para ignorar parcelas "x de")
        if not preco:
            # Pegamos todos os padrões de R$, mas ignoramos se houver um "x" ou "vezes" antes/depois (parcelas)
            texto_limpo = re.sub(r'\d+\s?[xX]\s?de\s?R\$\s?[\d.,]+', '', res.text) # Remove parcelas do texto antes de buscar
            match = re.search(r'R\$\s?(\d{1,3}(\.\d{3})*,\d{2})', texto_limpo)
            if match:
                preco = f"💰 *Apenas: {match.group(0)}*"
        
        if not preco:
            preco = "🔥 *VEJA O PREÇO NO SITE!*"
            
        return nome, img_url, preco
    except:
        return None, None, None

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

    enviados = 0
    meta = 3
    nichos = config.get("nichos", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if enviados >= meta: break
        sites = config.get("sites", [])
        random.shuffle(sites)
        
        for site in sites:
            if enviados >= meta: break
            
            # FILTRO ESPECIAL MERCADO LIVRE: Se for ML e o nicho for esporte, pula se não for luta/corrida
            # Nota: Isso assume que você tem um ID no nicho chamado 'esportes'
            termo = random.choice(nicho["termos"])
            
            # Lógica para evitar coletivos no ML (ajuste conforme os nomes no seu Categories.json)
            if "mercadolivre" in site['nome'].lower() and nicho['id'] == "esportes":
                termos_permitidos = ["luta", "boxe", "jiu jitsu", "corrida", "tenis de corrida", "kimono"]
                if not any(x in termo.lower() for x in termos_permitidos):
                    continue

            print(f"🔎 Buscando: {termo} na {site['nome']}")
            
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links_brutos = [a['href'] for a in soup.find_all('a', href=True)]
                links_limpos = []
                
                for l in links_brutos:
                    if not any(x in l for x in ["/p/", "/dp/", "/item/", "produto"]): continue
                    if l.startswith("http"): links_limpos.append(l)
                    elif l.startswith("//"): links_limpos.append("https:" + l)
                    else:
                        base = "https://www.netshoes.com.br" if "netshoes" in site['nome'].lower() else \
                               "https://www.zattini.com.br" if "zattini" in site['nome'].lower() else \
                               "https://www.mercadolivre.com.br"
                        links_limpos.append(base + ("" if l.startswith("/") else "/") + l)

                random.shuffle(links_limpos)
                
                for link in links_limpos:
                    if link not in history:
                        nome, img, preco = extrair_detalhes(link)
                        if not nome or any(x in nome for x in ["Netshoes", "Zattini", "Mercado Livre"]) or len(nome) < 15:
                            continue 

                        link_af = converter_afiliado(link, site["nome"], afiliados)
                        frase = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                        msg = f"{frase}\n\n📦 *{nome[:90]}...*\n\n{preco}\n\n🛒 Loja: {site['nome'].upper()}"
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 VER PREÇO / COMPRAR", url=link_af)]])

                        try:
                            if img and img.startswith("http"):
                                bot.send_photo(chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                            else:
                                bot.send_message(chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                            
                            history.append(link)
                            enviados += 1
                            print(f"✅ Enviado: {nome[:30]}")
                            time.sleep(10)
                            break
                        except: continue
            except: continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-500:], f, indent=2)

if __name__ == "__main__":
    main()
