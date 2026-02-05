import os
import json
import random
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Arquivos de configuração
HISTORY_FILE = "history.json"
AFFILIATES_FILE = "Affiliates.json"
CATEGORIES_FILE = "Categories.json"
COPY_FILE = "Copy.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

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

def minerar_produtos(site_url, site_nome):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    links_validos = []
    try:
        res = requests.get(site_url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filtro expandido para capturar mais produtos
            if any(x in href.lower() for x in ["/p/", "/item/", "/dp/", "produto", "itm", "shopping", "p-"]):
                if not href.startswith("http"):
                    if "amazon" in site_nome: href = "https://www.amazon.com.br" + href
                    elif "netshoes" in site_nome: href = "https://www.netshoes.com.br" + href
                    elif "zattini" in site_nome: href = "https://www.zattini.com.br" + href
                links_validos.append(href)
    except Exception as e:
        print(f"⚠️ Erro ao minerar {site_nome}: {e}")
    return list(set(links_validos))

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)
    
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    
    config_busca = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)

    sites = config_busca.get("sites", [])
    nichos = config_busca.get("nichos", [])
    
    random.shuffle(nichos)
    enviados_total = 0

    print(f"--- Iniciando Rodada (Histórico: {len(history)} links) ---")

    for nicho in nichos:
        if enviados_total >= 2: break 

        for site in sites:
            termo = random.choice(nicho["termos"])
            url_busca = site["url"] + termo.replace(" ", "+")
            print(f"🔎 Buscando '{termo}' em {site['nome']}...")
            
            links = minerar_produtos(url_busca, site["nome"])
            random.shuffle(links) # Embaralha para não pegar sempre o mesmo

            for link in links:
                if link not in history:
                    link_final = converter_para_afiliado(link, site["nome"], afiliados)
                    
                    frases = copies.get(nicho["id"], ["🔥 OFERTA IMPERDÍVEL!"])
                    msg = f"{random.choice(frases)}\n\n📦 *{termo.upper()}*\n\n🚀 Link promocional abaixo:"
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"🛒 VER NA {site['nome'].upper()}", url=link_final)]])
                    
                    try:
                        bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        history.append(link)
                        enviados_total += 1
                        print(f"✅ MENSAGEM ENVIADA: {termo}")
                        time.sleep(10) # Delay anti-spam
                        break 
                    except Exception as e:
                        print(f"❌ ERRO TELEGRAM: {e}")
                        continue
                else:
                    # Link já postado antes
                    continue

    if enviados_total == 0:
        print("🚨 ATENÇÃO: Nenhum produto novo foi enviado nesta rodada.")

    # Salva o histórico atualizado
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
