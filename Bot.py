import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO

# --- CONFIGURAÇÃO DE NICHOS ---
# Foco total em utilidades e itens que vendem bem em grupos de oferta
TERMOS_ML = ["quimono jiu jitsu", "whey protein", "creatina", "perfume importado"]
TERMOS_SHOPEE_CASA = ["organizador casa", "cozinha utilidades", "shopee choice", "decoração sala"]

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data if data else ([] if "History" in file else {})
            except: return [] if "History" in file else {}
    return [] if "History" in file else {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extrair_detalhes(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Título
        nome = soup.find("h1").get_text().strip() if soup.find("h1") else "Oferta Incrível"
        
        # Imagem (og:image é o mais estável)
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # Preço (Regex para pegar formato R$ XX,XX)
        precos = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', res.text)
        preco_final = f"R$ {precos[0]}" if precos else "Confira o preço!"

        if img_url:
            img_res = requests.get(img_url, timeout=15)
            return nome[:95], BytesIO(img_res.content), preco_final
    except: pass
    return None, None, None

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    if not token or not chat_id:
        print("❌ Erro: Variáveis de ambiente faltando.")
        return

    bot = Bot(token=token)
    history = load_json("History.json")
    afiliados = load_json("Affiliates.json")
    postados = 0

    # 1. PRIORIDADE MÁXIMA: MERCADO LIVRE
    print("🚀 [PRIORIDADE 1] ESTABILIZANDO MERCADO LIVRE...")
    for termo in random.sample(TERMOS_ML, 2):
        print(f"🔎 Buscando ML: {termo}")
        url_busca = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
        try:
            r = requests.get(url_busca, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            # Regex específica para pegar links de produtos MLB
            links = re.findall(r'https://produto\.mercadolivre\.com\.br/MLB-\d+-[^"\'\s]+', r.text)
            
            links_validos = [l for l in list(set(links)) if l not in history]
            for link in links_validos[:2]:
                nome, foto, preco = extrair_detalhes(link)
                if nome and foto:
                    tag_afiliado = afiliados.get("mercadolivre", "salvabjj-20") # Fallback se não carregar
                    link_final = f"{link}#id={tag_afiliado}"
                    
                    bot.send_photo(chat_id, photo=foto, 
                                 caption=f"💎 *MERCADO LIVRE*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [COMPRAR AGORA]({link_final})", 
                                 parse_mode="Markdown")
                    
                    history.append(link)
                    postados += 1
                    print(f"✅ ML Postado: {nome}")
                    time.sleep(12)
                    break
        except Exception as e:
            print(f"⚠️ Falha no ML para o termo {termo}: {e}")

    # 2. SEGUNDA PRIORIDADE: SHOPEE (CASA/CHOICE)
    if postados < 6:
        print("🏠 [PRIORIDADE 2] BUSCANDO SHOPEE CASA/CHOICE...")
        for termo in random.sample(TERMOS_SHOPEE_CASA, 2):
            # Usando busca via Google para evitar o bloqueio de bot da Shopee
            print(f"🔎 Buscando Shopee: {termo}")
            url_busca = f"https://www.google.com/search?q=site:shopee.com.br/product+{termo.replace(' ', '+')}"
            try:
                r = requests.get(url_busca, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                links = re.findall(r'https://shopee\.com\.br/[^&?\"\'\s]+', r.text)
                
                for link in list(set(links))[:2]:
                    if "universal-link" in link or link in history: continue
                    nome, foto, preco = extrair_detalhes(link)
                    if nome and foto:
                        bot.send_photo(chat_id, photo=foto, 
                                     caption=f"🏠 *SHOPEE CASA*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [VER NA SHOPEE]({link})", 
                                     parse_mode="Markdown")
                        history.append(link)
                        postados += 1
                        print(f"✅ Shopee Postado: {nome}")
                        time.sleep(12)
                        break
            except Exception as e:
                print(f"⚠️ Falha na Shopee: {e}")

    save_json("History.json", history[-500:])
    print(f"📊 Fim da execução. Total postado: {postados}")

if __name__ == "__main__":
    main()
