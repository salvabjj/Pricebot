import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO

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
        
        t = soup.find("h1") or soup.find("meta", property="og:title")
        nome = (t.get_text().strip() if t and not t.has_attr("content") else t["content"]) if t else "Produto Especial"
        
        # Detector de termos de bloqueio no título
        bloqueio = ["login", "signin", "captcha", "robot", "verificação", "acesso negado", "mercadolibre.com.br/gz/"]
        if any(b in nome.lower() or b in res.url.lower() for b in bloqueio):
            return None, None, None

        nome = re.sub(r'| Mercado Livre| | Amazon| | Netshoes| | Shopee', '', nome, flags=re.IGNORECASE).strip()

        # Tenta o PRINT para ML e Amazon
        if "amazon" in loja or "mercadolivre" in loja:
            img_url = f"https://s0.wp.com/mshots/v1/{url}?w=1024&h=768"
            # VALIDAR SE A IMAGEM ESTÁ PRONTA
            for _ in range(3):
                test_res = requests.get(img_url, timeout=10)
                if test_res.status_code == 200 and len(test_res.content) > 15000: # Se > 15kb, é uma imagem real
                    return nome[:100], BytesIO(test_res.content), "✅ *Preço no print da tela acima!*"
                time.sleep(5)
            print(f"⚠️ Print falhou para {loja_nome}, tentando foto limpa...")

        # FOTO LIMPA (Backup ou Padrão Shopee/Netshoes)
        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag else None
        
        texto_limpo = re.sub(r'\d+\s?[xX]\s?de\s?R\$\s?[\d.,]+', '', res.text)
        match = re.search(r'R\$\s?(\d{1,3}(\.\d{3})*,\d{2})', texto_limpo)
        preco = f"💰 *Apenas: {match.group(0)}*" if match else "🔥 *Confira o preço no site!*"
            
        return nome[:100], img, preco
    except:
        return None, None, None

# ... (Funções tratar_link e converter_afiliado permanecem iguais)

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)
    
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
                
                for l in random.sample(links, min(len(links), 10)):
                    url_real = tratar_link(l, site['nome'])
                    if url_real in history: continue
                    
                    nome, img, preco = extrair_detalhes(url_real, site['nome'])
                    
                    if nome and img:
                        url_af = converter_afiliado(url_real, site['nome'], afiliados)
                        msg = f"{random.choice(copies.get(nicho['id'], ['🔥 OFERTA!']))}\n\n📦 *{nome}*\n\n{preco}\n\n🛒 Loja: {site['nome'].upper()}"
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR AGORA", url=url_af)]])

                        try:
                            # Se for BytesIO (print), envia o arquivo, senão envia a URL
                            bot.send_photo(chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="Markdown")
                            history.append(url_real)
                            lojas_nesta_rodada.append(site['nome'])
                            total_enviados += 1
                            print(f"✅ Enviado: {site['nome']} ({total_enviados}/10)")
                            time.sleep(15)
                            break
                        except Exception as e:
                            print(f"Erro Telegram: {e}")
                            continue
            except: continue

    save_json(HISTORY_FILE, history[-500:])

# (tratar_link e converter_afiliado vêm aqui)
