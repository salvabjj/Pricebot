import os
import json
import random
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# --- CONFIGURAÇÕES DE ARQUIVOS ---
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
    """Insere automaticamente o seu ID de afiliado no link encontrado"""
    try:
        if "amazon" in site_nome.lower():
            tag = ids.get("amazon", "salvablessjj-20")
            return f"{url_pura}&tag={tag}" if "?" in url_pura else f"{url_pura}?tag={tag}"
        elif "shopee" in site_nome.lower():
            shopee_id = ids.get("shopee", "18308930971")
            return f"https://shopee.com.br/universal-link/{shopee_id}?url={url_pura}"
        elif "mercadolivre" in site_nome.lower():
            ml_id = ids.get("mercadolivre", "1561730990")
            return f"{url_pura}#id={ml_id}"
    except:
        return url_pura
    return url_pura

def minerar_produtos(site_url, site_nome):
    """Varre o site em busca de links de produtos reais"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    links_validos = []
    try:
        res = requests.get(site_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filtros de segurança para pegar apenas produtos
            if any(x in href for x in ["/p/", "/item/", "/dp/", "produto"]):
                if not href.startswith("http"):
                    if "amazon" in site_nome: href = "https://www.amazon.com.br" + href
                    elif "mercadolivre" in site_nome: href = href # ML costuma vir completo
                links_validos.append(href)
    except:
        pass
    return list(set(links_validos))

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    if not token or not chat_id:
        print("Erro: TELEGRAM_TOKEN ou CHAT_ID não configurados nos Secrets.")
        return

    bot = Bot(token=token)
    
    # Carregamento Seguro dos Dados
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    
    config_busca = load_json(CATEGORIES_FILE)
    afiliados = load_json(AFFILIATES_FILE)
    copies = load_json(COPY_FILE)

    sites = config_busca.get("sites", [])
    nichos = config_busca.get("nichos", [])
    
    enviados = 0
    random.shuffle(nichos) # Para cada execução focar em nichos diferentes

    for nicho in nichos:
        if enviados >= 5: break # Limite de envios por execução (20 min)

        # Tenta em todos os sites para este nicho
        for site in sites:
            termo = random.choice(nicho["termos"])
            url_busca = site["url"] + termo.replace(" ", "+")
            
            print(f"Buscando {termo} em {site['nome']}...")
            links = minerar_produtos(url_busca, site["nome"])
            
            for link in links:
                if link not in history:
                    link_final = converter_para_afiliado(link, site["nome"], afiliados)
                    
                    # Mensagem Profissional
                    prefixo = random.choice(copies.get(nicho["id"], ["🔥 OFERTA EXCLUSIVA!"]))
                    mensagem = f"{prefixo}\n\n📦 *{termo.upper()}*\n\n🚀 Aproveite antes que acabe no link abaixo:"
                    
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 COMPRAR COM DESCONTO", url=link_final)]])
                    
                    try:
                        bot.send_message(chat_id=chat_id, text=mensagem, reply_markup=kb, parse_mode="Markdown")
                        history.append(link)
                        enviados += 1
                        print(f"✅ Postado: {termo}")
                        time.sleep(15) # Pausa para evitar bloqueio do Telegram
                        break # Envia um desse nicho e pula para o próximo
                    except Exception as e:
                        print(f"Erro ao enviar Telegram: {e}")

    # Fallback: Se não achou nada novo na internet, usa a lista manual
    if enviados < 2:
        try:
            from Produtos import produtos
            # Lógica para pegar itens do arquivo Produtos.py se a mineração falhar
            print("Usando produtos do arquivo manual como fallback...")
            # (Adicione aqui o envio de 2 itens do Produtos.py se desejar)
        except ImportError:
            print("Arquivo Produtos.py não encontrado.")

    # Salva o histórico para não repetir
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
