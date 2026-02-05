import os
import json
import random
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# --- CONFIGURAÇÕES ---
HISTORY_FILE = "history.json"
AFFILIATES_FILE = "Affiliates.json"
CATEGORIES_FILE = "Categories.json"
COPY_FILE = "Copy.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def converter_para_afiliado(url_pura, site_nome, ids):
    """Transforma um link comum em link de afiliado"""
    try:
        if "amazon" in site_nome:
            tag = ids.get("amazon", "")
            return f"{url_pura}&tag={tag}" if "?" in url_pura else f"{url_pura}?tag={tag}"
        
        elif "mercadolivre" in site_nome:
            # Para ML, o ideal é usar a URL de redirecionamento do painel, 
            # mas aqui anexamos o ID de referência padrão.
            return f"{url_pura}#id={ids.get('mercadolivre')}"
            
        elif "shopee" in site_nome:
            # Estrutura de link universal Shopee
            shopee_id = ids.get("shopee")
            return f"https://shopee.com.br/universal-link/{shopee_id}?url={url_pura}"

        elif "netshoes" in site_nome:
            return f"{url_pura}?campaign={ids.get('netshoes')}"
    except:
        return url_pura
    return url_pura

def minerar_produtos(site_url, site_nome):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    links_encontrados = []
    try:
        res = requests.get(site_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filtro para pegar apenas links que pareçam produtos
            if any(x in href for x in ["/p/", "/item/", "/dp/", "produto"]):
                if not href.startswith("http"):
                    base = "https://www.amazon.com.br" if "amazon" in site_nome else ""
                    href = base + href
                links_encontrados.append(href)
    except:
        pass
    return list(set(links_encontrados))

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)

    # Carga de dados
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    
    config_busca = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)

    enviados_nesta_rodada = 0
    
    # Misturar nichos e sites para diversidade
    nichos = config_busca.get("nichos", [])
    sites = config_busca.get("sites", [])
    random.shuffle(nichos)

    for nicho in nichos:
        if enviados_nesta_rodada >= 3: break # Limite por execução para não ser banido

        for site in sites:
            termo = random.choice(nicho["termos"])
            url_busca = site["url"] + termo.replace(" ", "+")
            
            print(f"Buscando {termo} em {site['nome']}...")
            links = minerar_produtos(url_busca, site["nome"])
            
            for link in links:
                if link not in history:
                    # CONVERSÃO AUTOMÁTICA
                    link_afiliado = converter_para_afiliado(link, site["nome"], afiliados)
                    
                    # MONTAGEM DA MENSAGEM
                    prefixo = random.choice(copies.get(nicho["id"], ["🔥 OFERTA!"]))
                    msg = f"{prefixo}\n\n📦 *{termo.upper()}*\n\n🚀 Confira essa oportunidade no link abaixo:"
                    
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 VER OFERTA", url=link_afiliado)]])
                    
                    try:
                        bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb, parse_mode="Markdown")
                        history.append(link)
                        enviados_nesta_rodada += 1
                        time.sleep(15) # Delay entre mensagens
                        break # Pula para o próximo nicho após um envio bem sucedido
                    except Exception as e:
                        print(f"Erro Telegram: {e}")

    # FALLBACK: Se não enviou nada, envia um "Choice" fixo do arquivo Produtos.py
    if enviados_nesta_rodada < 2:
        print("Usando fallback (Choice)...")
        # [Aqui você pode repetir a lógica de ler o Produtos.py conforme as versões anteriores]

    # Salvar Histórico
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
