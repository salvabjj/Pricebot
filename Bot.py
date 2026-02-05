import os
import json
import random
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# NOMES COM PRIMEIRA LETRA MAIÚSCULA
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

def extrair_detalhes_produto(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Tenta pegar a imagem (og:image é o padrão de redes sociais)
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # Tenta pegar o nome real do produto
        title_tag = soup.find("meta", property="og:title")
        nome_produto = title_tag["content"] if title_tag else "Produto em Oferta"

        return nome_produto, img_url
    except:
        return None, None

def converter_para_afiliado(url_pura, site_nome, ids):
    site = site_nome.lower()
    if "amazon" in site:
        tag = ids.get("amazon", "salvablessjj-20")
        return f"{url_pura}&tag={tag}" if "?" in url_pura else f"{url_pura}?tag={tag}"
    elif "shopee" in site:
        s_id = ids.get("shopee", "18308930971")
        return f"https://shopee.com.br/universal-link/{s_id}?url={url_pura}"
    elif "mercadolivre" in site:
        return f"{url_pura}#id={ids.get('mercadolivre', '1561730990')}"
    elif "netshoes" in site or "zattini" in site:
        return f"{url_pura}?campaign={ids.get('netshoes', 'rWODdSNWJGM')}"
    return url_pura

def minerar_links(site_url, site_nome):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    links = []
    try:
        res = requests.get(site_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(x in href.lower() for x in ["/p/", "/item/", "/dp/"]):
                if not href.startswith("http"):
                    href = f"https://www.{site_nome.lower()}.com.br{href}"
                links.append(href)
    except: pass
    return list(set(links))

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)
    
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    
    config = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)

    random.shuffle(config.get("nichos", []))
    enviados = 0

    for nicho in config.get("nichos", []):
        if enviados >= 2: break

        for site in config.get("sites", []):
            if nicho["id"] == "choice" and "shopee" not in site["nome"]: continue
            
            termo = random.choice(nicho["termos"])
            links = minerar_links(site["url"] + termo.replace(" ", "+"), site["nome"])
            
            for link in links:
                if link not in history:
                    nome_real, img = extrair_detalhes_produto(link)
                    link_afiliado = converter_para_afiliado(link, site["nome"], afiliados)
                    
                    frase = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                    
                    # Montagem da Mensagem com Nome Real do Produto
                    mensagem = f"{frase}\n\n📦 *{nome_real[:80]}...*\n\n💰 *Preço Promocional na {site['nome'].upper()}*"
                    
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 IR PARA LOJA", url=link_afiliado)]])
                    
                    try:
                        if img:
                            bot.send_photo(chat_id=chat_id, photo=img, caption=mensagem, reply_markup=kb, parse_mode="Markdown")
                        else:
                            bot.send_message(chat_id=chat_id, text=mensagem, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(link)
                        enviados += 1
                        time.sleep(15)
                        break
                    except: continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
