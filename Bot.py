import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot
from io import BytesIO

# Configurações de Busca - Foco em Casa/Choice e Alta Conversão
TERMOS_ML = ["quimono jiu jitsu", "whey protein", "creatina", "perfume masculino"]
TERMOS_SHOPEE = ["organizador casa", "shopee choice", "utensilios cozinha", "decoração"]

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return [] if "History" in file else {}
    return [] if "History" in file else {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extrair_detalhes(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=20)
        if res.status_code != 200: return None, None, None
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Título
        nome = soup.find("h1").get_text().strip() if soup.find("h1") else "Oferta Especial"
        
        # Imagem - Tentativa em múltiplas tags para garantir
        img_url = None
        og_img = soup.find("meta", property="og:image")
        if og_img:
            img_url = og_img["content"]
        
        # Preço - Busca por padrão de Real (R$ XX,XX)
        precos = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', res.text)
        preco = f"R$ {precos[0]}" if precos else "Confira no site"
        
        if img_url:
            img_res = requests.get(img_url, timeout=10)
            return nome[:90], BytesIO(img_res.content), preco
    except:
        pass
    return None, None, None

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    history = load_json("History.json")
    postados = 0

    # --- MERCADO LIVRE ---
    print("🚀 BUSCANDO MERCADO LIVRE...")
    termo = random.choice(TERMOS_ML)
    url_ml = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
    try:
        r = requests.get(url_ml, headers=get_headers(), timeout=15)
        # Busca links que contenham MLB (anúncios)
        links = list(set(re.findall(r'https://produto\.mercadolivre\.com\.br/MLB-\d+-[^"\'\s]+', r.text)))
        
        for link in links:
            link_clean = link.split('#')[0]
            if link_clean in history: continue
            
            nome, foto, preco = extrair_detalhes(link_clean)
            if nome and foto:
                bot.send_photo(chat_id, photo=foto, caption=f"💎 *MERCADO LIVRE*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [COMPRAR AGORA]({link_clean})", parse_mode="Markdown")
                history.append(link_clean)
                postados += 1
                print(f"✅ ML: {nome}")
                break # Posta um e vai para a próxima loja
    except Exception as e:
        print(f"Erro ML: {e}")

    # --- SHOPEE (Via Google para evitar Block) ---
    print("🏠 BUSCANDO SHOPEE CASA/CHOICE...")
    termo_sh = random.choice(TERMOS_SHOPEE)
    url_google = f"https://www.google.com/search?q=site:shopee.com.br/product+{termo_sh.replace(' ', '+')}"
    try:
        r = requests.get(url_google, headers=get_headers(), timeout=15)
        links_sh = list(set(re.findall(r'https://shopee\.com\.br/[^&?\"\'\s]+', r.text)))
        
        for link in links_sh:
            if "universal-link" in link or link in history: continue
            nome, foto, preco = extrair_detalhes(link)
            if nome and foto:
                bot.send_photo(chat_id, photo=foto, caption=f"🏠 *SHOPEE CASA*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [VER NA SHOPEE]({link})", parse_mode="Markdown")
                history.append(link)
                postados += 1
                print(f"✅ Shopee: {nome}")
                break
    except Exception as e:
        print(f"Erro Shopee: {e}")

    save_json("History.json", history[-500:])
    print(f"📊 Relatório: {postados} ofertas postadas.")

if __name__ == "__main__":
    main()
