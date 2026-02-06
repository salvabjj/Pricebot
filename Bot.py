import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot
from io import BytesIO

# --- [P] PRIORIDADE DE NICHOS ---
TERMOS_ML = ["quimono jiu jitsu", "whey protein", "creatina", "perfume masculino"]
TERMOS_SHOPEE_CASA = ["organizador casa", "shopee choice", "utensilios cozinha", "decoração sala"]

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.google.com/"
    }

# --- [T] TRATAMENTO DE DADOS ---
def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return []
    return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- [S] SCRAPING RESILIENTE ---
def extrair_detalhes(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=20)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        nome = soup.find("h1").get_text().strip() if soup.find("h1") else "Oferta Especial"
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # Regex para capturar preços no formato R$ 100,00 ou 100,00
        precos = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', res.text)
        preco = f"R$ {precos[0]}" if precos else "Confira no site"
        
        if img_url:
            img_res = requests.get(img_url, timeout=15)
            return nome[:90], BytesIO(img_res.content), preco
    except: pass
    return None, None, None

def main():
    # --- [C] CONFORMIDADE COM AMBIENTE ---
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)
    history = load_json("History.json")
    postados = 0

    # --- [R] RESILIÊNCIA DE BUSCA ---
    # Passo 1: Mercado Livre
    print("🚀 Buscando Mercado Livre...")
    termo = random.choice(TERMOS_ML)
    url_ml = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
    try:
        r = requests.get(url_ml, headers=get_headers(), timeout=15)
        # Captura links MLB usando Regex (mais estável que BS4)
        links = list(set(re.findall(r'https://produto\.mercadolivre\.com\.br/MLB-\d+-[^"\'\s]+', r.text)))
        
        for link in links:
            if link in history: continue
            nome, foto, preco = extrair_detalhes(link)
            if nome and foto:
                bot.send_photo(chat_id, photo=foto, 
                             caption=f"💎 *MERCADO LIVRE*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [COMPRAR AGORA]({link})", 
                             parse_mode="Markdown")
                history.append(link)
                postados += 1
                print(f"✅ ML: {nome}")
                break # Posta um e encerra para evitar spam/ban
    except Exception as e: print(f"Erro ML: {e}")

    # Passo 2: Shopee (Disfarçado via Google para evitar block)
    if postados == 0:
        print("🏠 Buscando Shopee Casa/Choice...")
        termo_sh = random.choice(TERMOS_SHOPEE_CASA)
        url_google = f"https://www.google.com/search?q=site:shopee.com.br/product+{termo_sh.replace(' ', '+')}"
        try:
            r = requests.get(url_google, headers=get_headers(), timeout=15)
            links_sh = list(set(re.findall(r'https://shopee\.com\.br/[^&?\"\'\s]+', r.text)))
            for link in links_sh:
                if "universal-link" in link or link in history: continue
                nome, foto, preco = extrair_detalhes(link)
                if nome and foto:
                    bot.send_photo(chat_id, photo=foto, 
                                 caption=f"🏠 *SHOPEE CASA*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [VER NA SHOPEE]({link})", 
                                 parse_mode="Markdown")
                    history.append(link)
                    postados += 1
                    print(f"✅ Shopee: {nome}")
                    break
        except Exception as e: print(f"Erro Shopee: {e}")

    save_json("History.json", history[-300:])
    print(f"📊 Relatório: {postados} ofertas postadas.")

if __name__ == "__main__":
    main()        titulo = soup.find("h1").get_text().strip() if soup.find("h1") else "Oferta Especial"
        
        # Imagem: Busca na tag OpenGraph (mais estável)
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # Preço: Regex para encontrar o padrão R$ ou valores decimais
        precos = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', res.text)
        preco = f"R$ {precos[0]}" if precos else "Confira no site"
        
        if img_url:
            img_res = requests.get(img_url, timeout=15)
            return titulo[:90], BytesIO(img_res.content), preco
    except:
        pass
    return None, None, None

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    history = load_json("History.json")
    postados = 0

    # --- ETAPA 1: MERCADO LIVRE (Busca Direta por Regex) ---
    print("🚀 TENTANDO MERCADO LIVRE...")
    termo_ml = random.choice(TERMOS_ML)
    url_ml = f"https://lista.mercadolivre.com.br/{termo_ml.replace(' ', '-')}"
    try:
        r = requests.get(url_ml, headers=get_headers(), timeout=15)
        # Regex: Procura qualquer link que siga o padrão de produto do ML (MLB-xxxx)
        links = list(set(re.findall(r'https://produto\.mercadolivre\.com\.br/MLB-\d+-[^"\'\s]+', r.text)))
        
        for link in links:
            link_limpo = link.split('#')[0]
            if link_limpo in history: continue
            
            nome, foto, preco = extrair_dados_basicos(link_limpo)
            if nome and foto:
                bot.send_photo(chat_id, photo=foto, 
                             caption=f"💎 *MERCADO LIVRE*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [COMPRAR AGORA]({link_limpo})", 
                             parse_mode="Markdown")
                history.append(link_limpo)
                postados += 1
                print(f"✅ ML Postado: {nome}")
                break # Posta apenas um por execução para evitar ban
    except Exception as e:
        print(f"❌ Erro ML: {e}")

    # --- ETAPA 2: SHOPEE (Busca via Google para burlar bloqueio) ---
    if postados == 0: # Se não postou ML, tenta Shopee
        print("🏠 TENTANDO SHOPEE (CASA/CHOICE)...")
        termo_sh = random.choice(TERMOS_SHOPEE)
        # Truque: O Google raramente bloqueia o GitHub Actions. Usamos ele como ponte.
        url_ponte = f"https://www.google.com/search?q=site:shopee.com.br/product+{termo_sh.replace(' ', '+')}"
        try:
            r = requests.get(url_ponte, headers=get_headers(), timeout=15)
            links_sh = list(set(re.findall(r'https://shopee\.com\.br/[^&?\"\'\s]+', r.text)))
            
            for link in links_sh:
                if "universal-link" in link or link in history: continue
                nome, foto, preco = extrair_dados_basicos(link)
                if nome and foto:
                    bot.send_photo(chat_id, photo=foto, 
                                 caption=f"🏠 *SHOPEE CASA*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [VER NA SHOPEE]({link})", 
                                 parse_mode="Markdown")
                    history.append(link)
                    postados += 1
                    print(f"✅ Shopee Postado: {nome}")
                    break
        except Exception as e:
            print(f"❌ Erro Shopee: {e}")

    save_json("History.json", history[-300:])
    print(f"📊 Fim: {postados} ofertas enviadas.")

if __name__ == "__main__":
    main()
    
