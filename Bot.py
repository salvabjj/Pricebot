import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO

# Configurações de busca
TERMOS_ML = ["quimono jiu jitsu", "whey protein", "creatina", "perfume masculino"]
TERMOS_SHOPEE_CASA = ["organizador de casa", "shopee choice casa", "decoração sala", "utensilios cozinha"]

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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Nome do produto
        nome = soup.find("h1").get_text().strip() if soup.find("h1") else "Oferta Especial"
        
        # Imagem
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # Preço (Regex mais flexível)
        precos = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', res.text)
        preco = f"R$ {precos[0]}" if precos else "Confira no site"
        
        if img_url:
            img_res = requests.get(img_url, timeout=10)
            return nome[:90], BytesIO(img_res.content), preco
    except Exception as e:
        print(f"DEBUG: Falha ao extrair {url}: {e}")
    return None, None, None

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    history = load_json("History.json")
    afiliados = load_json("Affiliates.json")
    
    postados = 0

    # --- BLOCO MERCADO LIVRE (PRIORIDADE 1) ---
    print("🚀 TENTANDO MERCADO LIVRE...")
    for termo in random.sample(TERMOS_ML, 2):
        search_url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
        try:
            r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            # Busca links que contenham o padrão de produto do ML
            links = re.findall(r'(https://produto\.mercadolivre\.com\.br/MLB-\d+-[^"]+)', r.text)
            
            for link in list(set(links))[:3]:
                link_limpo = link.split('#')[0]
                if link_limpo in history: continue
                
                nome, foto, preco = extrair_detalhes(link_limpo)
                if nome and foto:
                    link_afiliado = f"{link_limpo}#id={afiliados.get('mercadolivre', 'default')}"
                    bot.send_photo(chat_id, photo=foto, caption=f"💎 *MERCADO LIVRE*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [COMPRAR AGORA]({link_afiliado})", parse_mode="Markdown")
                    history.append(link_limpo)
                    postados += 1
                    print(f"✅ ML postado: {nome}")
                    time.sleep(10)
                    break
        except Exception as e: print(f"Erro no ML: {e}")

    # --- BLOCO SHOPEE (CASA E CHOICE) ---
    if postados < 5:
        print("🏠 TENTANDO SHOPEE (CASA/CHOICE)...")
        # Usando a busca do Google para burlar o bloqueio direto da Shopee no GitHub Actions
        for termo in random.sample(TERMOS_SHOPEE_CASA, 2):
            search_url = f"https://www.google.com/search?q=site:shopee.com.br+{termo.replace(' ', '+')}"
            try:
                r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                links = re.findall(r'https://shopee\.com\.br/[^&?\"\'\s]+', r.text)
                
                for link in list(set(links))[:3]:
                    if "universal-link" in link or link in history: continue
                    
                    nome, foto, preco = extrair_detalhes(link)
                    if nome and foto:
                        # Aqui você deve colocar seu link de afiliado da Shopee
                        bot.send_photo(chat_id, photo=foto, caption=f"🏠 *SHOPEE CASA*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [VER NA SHOPEE]({link})", parse_mode="Markdown")
                        history.append(link)
                        postados += 1
                        print(f"✅ Shopee postado: {nome}")
                        time.sleep(10)
                        break
            except Exception as e: print(f"Erro na Shopee: {e}")

    save_json("History.json", history[-500:]) # Mantém apenas os últimos 500
    print(f"📊 Fim da execução. Postados: {postados}")

if __name__ == "__main__":
    main()
