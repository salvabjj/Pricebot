import os
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from telegram import Bot, ParseMode

# ==========================
# CONFIGURAÇÕES GERAIS
# ==========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HISTORY_FILE = "history.json"
MIN_PRODUTOS_POR_EXECUCAO = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ==========================
# LINKS BASE (AFILIADOS)
# ==========================
AMAZON_TAG = "salvablessjj-20"

SITES = {
    "Amazon": [
        "https://www.amazon.com.br/s?k=tenis+esportivo",
        "https://www.amazon.com.br/s?k=suplemento",
        "https://www.amazon.com.br/s?k=eletronicos"
    ],
    "Shopee": [
        "https://shopee.com.br/search?keyword=tenis",
        "https://shopee.com.br/search?keyword=camisa+esportiva"
    ],
    "Mercado Livre": [
        "https://lista.mercadolivre.com.br/tenis-esportivo",
        "https://lista.mercadolivre.com.br/suplementos"
    ],
    "Netshoes": [
        "https://www.netshoes.com.br/tenis",
        "https://www.netshoes.com.br/camisas"
    ]
}

# ==========================
# HISTÓRICO
# ==========================
def carregar_historico():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_historico(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# ==========================
# UTILIDADES
# ==========================
def normalizar_link_amazon(link):
    if "/dp/" in link:
        produto = link.split("/dp/")[1].split("/")[0]
        return f"https://www.amazon.com.br/dp/{produto}?tag={AMAZON_TAG}"
    return link

def ja_enviado(link, history):
    return link in history

# ==========================
# SCRAPERS
# ==========================
def buscar_amazon(url):
    produtos = []
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    for item in soup.select("div[data-component-type='s-search-result']"):
        try:
            link = "https://www.amazon.com.br" + item.h2.a["href"]
            link = normalizar_link_amazon(link)

            titulo = item.h2.text.strip()
            img = item.img["src"] if item.img else None

            produtos.append({
                "site": "Amazon",
                "titulo": titulo,
                "link": link,
                "imagem": img
            })
        except:
            continue

    return produtos

def buscar_simples(url, site_nome):
    produtos = []
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        link = a["href"]
        if link.startswith("/"):
            continue
        if site_nome.lower() not in link.lower():
            continue

        produtos.append({
            "site": site_nome,
            "titulo": a.text.strip()[:80],
            "link": link,
            "imagem": None
        })

    return produtos

# ==========================
# COLETAR PRODUTOS
# ==========================
def coletar_produtos():
    todos = []

    for site, urls in SITES.items():
        for url in urls:
            try:
                if site == "Amazon":
                    todos.extend(buscar_amazon(url))
                else:
                    todos.extend(buscar_simples(url, site))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"Erro em {site}: {e}")

    return todos

# ==========================
# ENVIO TELEGRAM
# ==========================
def enviar_produto(bot, produto):
    texto = (
        f"🔥 *OFERTA IMPERDÍVEL*\n\n"
        f"🛍️ *{produto['titulo']}*\n"
        f"🌐 {produto['site']}\n\n"
        f"👉 [COMPRAR AGORA]({produto['link']})"
    )

    if produto["imagem"]:
        bot.send_photo(
            chat_id=CHAT_ID,
            photo=produto["imagem"],
            caption=texto,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        bot.send_message(
            chat_id=CHAT_ID,
            text=texto,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=False
        )

# ==========================
# MAIN
# ==========================
def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    history = carregar_historico()

    produtos = coletar_produtos()
    random.shuffle(produtos)

    enviados = 0

    for produto in produtos:
        if enviados >= MIN_PRODUTOS_POR_EXECUCAO:
            break

        if ja_enviado(produto["link"], history):
            continue

        enviar_produto(bot, produto)
        history.append(produto["link"])
        enviados += 1
        time.sleep(random.uniform(2, 4))

    salvar_historico(history)

    if enviados == 0:
        bot.send_message(
            chat_id=CHAT_ID,
            text="⚠️ Nenhuma oferta nova encontrada nesta execução."
        )

if __name__ == "__main__":
    main()