import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot
from io import BytesIO

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.google.com/"
    }

def extrair_bruto(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=20)
        if res.status_code != 200: return None, None, None
        
        # Extração via Meta Tags (Padrão mais estável do mercado)
        soup = BeautifulSoup(res.text, "html.parser")
        titulo = soup.find("meta", property="og:title")["content"] if soup.find("meta", property="og:title") else "Oferta"
        img_url = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else None
        
        # Busca preço via padrão numérico R$
        precos = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', res.text)
        preco = f"R$ {precos[0]}" if precos else "Ver preço"
        
        if img_url:
            img_res = requests.get(img_url, timeout=15)
            return titulo[:90], BytesIO(img_res.content), preco
    except: pass
    return None, None, None

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    
    # 🚀 BUSCA MERCADO LIVRE (Regex MLB)
    print("🔎 Varrendo Mercado Livre...")
    termo = random.choice(["whey protein", "quimono jiu jitsu", "creatina"])
    r = requests.get(f"https://lista.mercadolivre.com.br/{termo}", headers=get_headers())
    links = re.findall(r'https://produto\.mercadolivre\.com\.br/MLB-\d+-[^"\'\s]+', r.text)
    
    for link in list(set(links))[:2]:
        nome, foto, preco = extrair_bruto(link)
        if nome and foto:
            bot.send_photo(chat_id, photo=foto, caption=f"💎 *ML*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [COMPRAR]({link})", parse_mode="Markdown")
            print(f"✅ ML Postado")
            return

    # 🏠 BUSCA SHOPEE (Via Google)
    print("🔎 Varrendo Shopee...")
    termo_sh = random.choice(["organizador casa", "utensilios cozinha"])
    r_sh = requests.get(f"https://www.google.com/search?q=site:shopee.com.br/product+{termo_sh}", headers=get_headers())
    links_sh = re.findall(r'https://shopee\.com\.br/[^&?\"\'\s]+', r_sh.text)
    
    for link in list(set(links_sh))[:2]:
        nome, foto, preco = extrair_bruto(link)
        if nome and foto:
            bot.send_photo(chat_id, photo=foto, caption=f"🏠 *SHOPEE*\n\n📦 {nome}\n💰 *{preco}*\n\n🛒 [COMPRAR]({link})", parse_mode="Markdown")
            print(f"✅ Shopee Postado")
            break

if __name__ == "__main__":
    main()
