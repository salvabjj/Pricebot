import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO
from datetime import datetime

# Arquivos
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

def extrair_detalhes(url, loja_nome):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return None, None, None
        soup = BeautifulSoup(res.text, "html.parser")
        
        t = soup.find("h1") or soup.find("meta", property="og:title")
        nome = (t.get_text().strip() if t and not t.has_attr("content") else t["content"]) if t else "Oferta"
        
        img_tag = soup.find("meta", property="og:image:secure_url") or soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        texto = res.text.replace('\n', ' ').replace('\xa0', ' ')
        precos = re.findall(r'(?:R\$|R\$\s?|Price:)\s?([\d\.]+\,\d{2})', texto)
        preco_final = f"💰 *Preço: R$ {precos[0]}*" if precos else "🔥 *Confira o valor no site!*"

        img_res = requests.get(img_url, headers=headers, timeout=10)
        if img_res.status_code == 200:
            return nome[:100], BytesIO(img_res.content), preco_final
        return None, None, None
    except: return None, None, None

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    
    history = load_json(HISTORY_FILE)
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)
    
    stats = {"enviados": 0, "lojas": {}}
    
    # --- CONFIGURAÇÃO DE NICHOS POR LOJA ---
    termos_ml_amazon = ["jiu jitsu", "suplemento whey", "creatina", "iphone", "smartphone", "perfume", "tênis"]
    termos_shopee = ["casa e decoração", "organizador", "cozinha utilidades", "shopee choice", "itens casa"]

    # 1. PRIORIDADE ABSOLUTA: MERCADO LIVRE
    print("🚀 ESTABILIZANDO MERCADO LIVRE...")
    ml_site = next((s for s in config['sites'] if "mercadolivre" in s['nome'].lower()), None)
    if ml_site:
        for termo in random.sample(termos_ml_amazon, 3):
            print(f"🔎 Tentando ML com: {termo}")
            try:
                r = requests.get(ml_site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in soup.find_all('a', href=True) if "MLB-" in a['href']]
                random.shuffle(links)
                for l in links[:5]:
                    url_f = limpar_url(l)
                    if url_f in history: continue
                    nome, foto, valor = extrair_detalhes(url_f, "Mercado Livre")
                    if nome and foto:
                        url_af = f"{url_f}#id={afiliados.get('mercadolivre')}"
                        bot.send_photo(chat_id, photo=foto, caption=f"🔥 MERCADO LIVRE\n\n📦 *{nome}*\n\n{valor}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 COMPRAR", url=url_af)]]))
                        history.append(url_f)
                        stats["enviados"] += 1
                        stats["lojas"]["Mercado Livre"] = 1
                        print("✅ ML ESTABILIZADO!")
                        time.sleep(15)
                        break
                if "Mercado Livre" in stats["lojas"]: break
            except Exception as e: print(f"❌ Erro ML: {e}")

    # 2. PRIORIDADE: AMAZON
    print("⭐ PRIORIDADE: AMAZON")
    amz_site = next((s for s in config['sites'] if "amazon" in s['nome'].lower()), None)
    if amz_site and stats["enviados"] < 10:
        # Lógica similar para Amazon... (omitida para brevidade, mas segue o mesmo padrão de busca)
        pass

    # 3. PRIORIDADE: SHOPEE (FOCADA EM CASA/CHOICE)
    print("🏠 PRIORIDADE: SHOPEE (CASA/CHOICE)")
    shp_site = next((s for s in config['sites'] if "shopee" in s['nome'].lower()), None)
    if shp_site and stats["enviados"] < 10:
        for termo in random.sample(termos_shopee, 2):
            print(f"🔎 Buscando Shopee Choice/Casa: {termo}")
            # Lógica de extração Shopee...
            pass

    save_json(HISTORY_FILE, history[-600:])
    print(f"📊 Relatório: {stats['enviados']} ofertas postadas.")

if __name__ == "__main__":
    main()
