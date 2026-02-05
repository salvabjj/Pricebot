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

def extrair_dados_loja(soup, url):
    preco_de = None
    preco_por = None
    
    if "amazon.com.br" in url:
        # Lógica Amazon
        p_de = soup.find("span", class_="a-price a-text-price")
        p_por = soup.find("span", class_="a-price-whole")
        if p_de: preco_de = p_de.get_text().replace("R$", "").strip()
        if p_por: preco_por = p_por.get_text().strip()
            
    elif "netshoes.com.br" in url or "zattini.com.br" in url:
        # Lógica Netshoes/Zattini
        p_de = soup.find("del")
        p_por = soup.find("strong", {"itemprop": "price"})
        if p_de: preco_de = p_de.get_text().replace("R$", "").strip()
        if p_por: preco_por = p_por.get_text().replace("R$", "").strip()

    elif "mercadolivre.com.br" in url:
        # Lógica Mercado Livre
        p_de = soup.find("span", class_="andes-money-amount__fraction")
        if p_de: preco_por = p_de.get_text().strip()

    return preco_de, preco_por

def extrair_detalhes_completo(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 1. Tenta pegar a imagem
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # 2. Tenta pegar o nome
        title_tag = soup.find("meta", property="og:title")
        nome = title_tag["content"].split("|")[0].strip() if title_tag else "Produto em Oferta"
        
        # 3. Tenta pegar os preços
        preco_de, preco_por = extrair_dados_loja(soup, url)

        return nome, img_url, preco_de, preco_por
    except:
        return None, None, None, None

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
            termo = random.choice(nicho["termos"])
            # Lógica simples de busca
            url_busca = site["url"] + termo.replace(" ", "+")
            
            # Aqui simplificamos a mineração (pegando os primeiros links /p/)
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                r = requests.get(url_busca, headers=headers, timeout=10)
                s = BeautifulSoup(r.text, "html.parser")
                links = [a['href'] for a in s.find_all('a', href=True) if "/p/" in a['href'] or "/dp/" in a['href']]
            except: links = []

            for link in list(set(links)):
                if not link.startswith("http"):
                    link = f"https://www.{site['nome'].lower()}.com.br" + (link if link.startswith("/") else "/" + link)

                if link not in history:
                    nome, img, p_de, p_por = extrair_detalhes_completo(link)
                    
                    if not p_por: continue # Se não achar o preço, pula para o próximo
                    
                    link_af = converter_para_afiliado(link, site["nome"], afiliados)
                    frase = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                    
                    # Montagem da mensagem com preços
                    txt_preco = f"💰 *Por: R$ {p_por}*"
                    if p_de:
                        txt_preco = f"❌ De: ~~R$ {p_de}~~\n✅ *Por: R$ {p_por}*"

                    msg = f"{frase}\n\n📦 *{nome[:70]}...*\n\n{txt_preco}\n\n🛒 Loja: {site['nome'].upper()}"
                    
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 IR PARA LOJA", url=link_af)]])
                    
                    try:
                        if img:
                            bot.send_photo(chat_id=chat_id, photo=img, caption=msg, reply_markup=kb, parse_mode="MarkdownV2" if "~~" in txt_preco else "Markdown")
                        else:
                            bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        
                        history.append(link)
                        enviados += 1
                        time.sleep(15)
                        break
                    except: continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
