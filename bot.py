import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ===============================
# CONFIGURAÇÕES TELEGRAM
# ===============================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ===============================
# LINKS POR CATEGORIA (EXEMPLO)
# depois você pode externalizar
# ===============================
CATEGORIAS = {
    "Eletrodomésticos": [
        "https://amzn.to/46iUEb6",
        "https://s.shopee.com.br/8KjpTzVMDC",
        "https://mercadolivre.com/sec/2TupDRd"
    ],
    "Moda Masculina": [
        "https://mercadolivre.com/sec/115emZK",
        "https://www.netshoes.com.br/p/tenis-couro-adidas-grand-court-alpha-masculino-marrom-FB9-8951-138"
    ]
}

# ===============================
# UTILIDADES
# ===============================
def resolver_link(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url


# ===============================
# AMAZON
# ===============================
def ler_amazon(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.select_one("#productTitle")
        preco = soup.select_one("#priceblock_ourprice, #priceblock_dealprice")
        imagem = soup.select_one("#imgTagWrapperId img")

        return {
            "nome": titulo.get_text(strip=True) if titulo else None,
            "preco": preco.get_text(strip=True) if preco else None,
            "imagem": imagem["src"] if imagem else None
        }
    except:
        return None


# ===============================
# SHOPEE
# ===============================
def ler_shopee(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.find("title")
        imagem = soup.find("meta", property="og:image")

        return {
            "nome": titulo.text.strip() if titulo else None,
            "preco": None,
            "imagem": imagem["content"] if imagem else None
        }
    except:
        return None


# ===============================
# MERCADO LIVRE
# ===============================
def ler_mercadolivre(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.find("h1")
        preco = soup.select_one(".andes-money-amount__fraction")
        imagem = soup.find("meta", property="og:image")

        return {
            "nome": titulo.text.strip() if titulo else None,
            "preco": f"R$ {preco.text}" if preco else None,
            "imagem": imagem["content"] if imagem else None
        }
    except:
        return None


# ===============================
# NETSHOES
# ===============================
def ler_netshoes(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.find("h1")
        imagem = soup.find("meta", property="og:image")

        return {
            "nome": titulo.text.strip() if titulo else None,
            "preco": None,
            "imagem": imagem["content"] if imagem else None
        }
    except:
        return None


# ===============================
# IDENTIFICAR LOJA
# ===============================
def extrair_dados(url):
    url_final = resolver_link(url)

    if "amazon" in url_final:
        return ler_amazon(url_final), url_final
    if "shopee" in url_final:
        return ler_shopee(url_final), url_final
    if "mercadolivre" in url_final:
        return ler_mercadolivre(url_final), url_final
    if "netshoes" in url_final:
        return ler_netshoes(url_final), url_final

    return None, url_final


# ===============================
# ENVIO TELEGRAM
# ===============================
def enviar_produto(categoria, dados, link):
    nome = dados.get("nome") or "Produto em oferta"
    preco = dados.get("preco") or ""
    imagem = dados.get("imagem")

    texto = f"🔥 *{categoria}*\n\n*{nome}*\n{preco}"

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Ver oferta", url=link)]
    ])

    if imagem:
        bot.send_photo(
            chat_id=CHAT_ID,
            photo=imagem,
            caption=texto,
            parse_mode="Markdown",
            reply_markup=teclado
        )
    else:
        bot.send_message(
            chat_id=CHAT_ID,
            text=texto,
            parse_mode="Markdown",
            reply_markup=teclado
        )


# ===============================
# EXECUÇÃO PRINCIPAL
# ===============================
def main():
    enviados = 0

    for categoria, links in CATEGORIAS.items():
        for link in links:
            dados, link_final = extrair_dados(link)
            if dados and dados.get("nome"):
                enviar_produto(categoria, dados, link_final)
                enviados += 1

    if enviados == 0:
        bot.send_message(
            chat_id=CHAT_ID,
            text="⚠️ Nenhuma oferta encontrada nesta execução."
        )


if __name__ == "__main__":
    main()