import os, json, random, time, requests, re
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO

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

def extrair_detalhes(url, loja_nome):
    # Headers mais fortes para evitar bloqueio
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Pega Título
        t = soup.find("h1") or soup.find("meta", property="og:title")
        nome = (t.get_text().strip() if t and not t.has_attr("content") else t["content"]) if t else "Produto em Oferta"
        nome = re.sub(r'| Mercado Livre| | Amazon| | Netshoes| | Shopee', '', nome, flags=re.IGNORECASE).strip()

        # Tenta pegar Foto do Site (Mais rápido e seguro que print)
        img_tag = soup.find("meta", property="og:image") or soup.find("meta", name="twitter:image")
        img = img_tag["content"] if img_tag else None

        # Tenta pegar Preço
        # Procura por padrões de R$ 1.234,56
        precos = re.findall(r'R\$\s?[\d\.]+\,\d{2}', res.text)
        preco_final = f"💰 *Preço: {precos[0]}*" if precos else "🔥 *Confira o preço no site!*"
            
        return nome[:100], img, preco_final
    except Exception as e:
        print(f"Erro ao abrir link: {e}")
        return None, None, None

def tratar_link(link, loja_nome):
    if link.startswith("http"): return link
    base = ""
    if "mercadolivre" in loja_nome.lower(): base = "https://www.mercadolivre.com.br"
    elif "netshoes" in loja_nome.lower(): base = "https://www.netshoes.com.br"
    elif "shopee" in loja_nome.lower(): base = "https://shopee.com.br"
    elif "amazon" in loja_nome.lower(): base = "https://www.amazon.com.br"
    return base + ("" if link.startswith("/") else "/") + link

def converter_afiliado(url, site_nome, ids):
    s = site_nome.lower()
    if "amazon" in s: return f"{url}?tag={ids.get('amazon', 'salvablessjj-20')}"
    if "shopee" in s: return f"https://shopee.com.br/universal-link/{ids.get('shopee', '18308930971')}?url={url}"
    if "mercadolivre" in s: return f"{url}#id={ids.get('mercadolivre', '1561730990')}"
    return url

def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    
    history = load_json(HISTORY_FILE)
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)
    
    total_enviados = 0
    nichos = config.get("nichos", [])
    sites = config.get("sites", [])
    
    random.shuffle(nichos)
    
    for nicho in nichos:
        if total_enviados >= 10: break
        random.shuffle(sites)
        
        for site in sites:
            if total_enviados >= 10: break
            termo = random.choice(nicho["termos"])
            print(f"🔎 Buscando: {termo} em {site['nome']}")
            
            try:
                r = requests.get(site["url"] + termo.replace(" ", "+"), headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Pega links de produtos
                links = [a['href'] for a in soup.find_all('a', href=True) if any(x in a['href'] for x in ["/p/", "/dp/", "/item/", "MLB-", "-P_"])]
