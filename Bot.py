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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Nome
        title_tag = soup.find("meta", property="og:title") or soup.find("h1")
        nome = title_tag["content"] if title_tag and title_tag.has_attr("content") else (title_tag.get_text().strip() if title_tag else "Produto em Oferta")
        nome = nome.split('|')[0].strip()

        # Imagem
        img_tag = soup.find("meta", property="og:image") or soup.find("img")
        img_url = img_tag["content"] if img_tag and img_tag.has_attr("content") else (img_tag["src"] if img_tag and img_tag.has_attr("src") else None)
        
        # Preço - Busca agressiva
        match = re.search(r'R\$\s?(\d{1,3}(\.\d{3})*,\d{2})', res.text)
        preco = f"💰 *Apenas: {match.group(0)}*" if match else "🔥 *VEJA O PREÇO NO SITE!*"
            
        return nome, img_url, preco
    except:
        return None, None, None

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
        random.shuffle(sites) # Muda a ordem das lojas para não travar em uma
        
        for site in sites:
            if enviados >= meta: break
            termo = random.choice(nicho["termos"])
            print(f"Buscando: {termo} na {site['nome']}")
            
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Captura links e corrige URLs incompletas
                links_brutos = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/item/", "/dp/", "produto"])]
                
                links_limpos = []
                for l in links_brutos:
                    if l.startswith("http"):
                        links_limpos.append(l)
                    elif l.startswith("//"):
                        links_limpos.append("https:" + l)
                    else:
                        # Monta a URL base conforme a loja
                        base = "https://www.netshoes.com.br" if "netshoes" in site['nome'].lower() else \
                               "https://www.zattini.com.br" if "zattini" in site['nome'].lower() else \
                               "https://www.mercadolivre.com.br"
                        links_limpos.append(base + ("" if l.startswith("/") else "/") + l)

                random.shuffle(links_limpos)
                
                for link in links_limpos:
                    if link not in history:
                        nome, img, preco = extrair_detalhes(link)
                        
                        # Se não pegou nome, pula. Mas aceita quase tudo.
                        if not nome or len(nome) < 3: continue 

                        frase = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                        msg = f"{frase}\n\n📦 *{nome[:100]}*\n\n{preco}\n\n🛒 Loja: {site['nome'].upper()}"
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR AGORA", url=link)]])

                        if img and img.startswith("http"):
                            bot.send_photo(chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                        else:
                            bot.send_message(chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(link)
                        enviados += 1
                        print(f"✅ Sucesso {enviados}/{meta}")
                        time.sleep(8)
                        break
            except Exception as e:
                print(f"Erro na {site['nome']}: {e}")

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-300:], f)

if __name__ == "__main__":
    main()
