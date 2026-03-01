import requests
from bs4 import BeautifulSoup
from utils.parser import limpar_preco

def capturar():
    url = "https://www.zattini.com.br/tenis"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    produtos = []

    for item in soup.select(".product-card")[:40]:
        link = item.select_one("a")
        preco_atual = item.select_one(".price-por")

        if link and preco_atual:
            produtos.append({
                "loja": "Zattini",
                "titulo": link.get_text(strip=True),
                "link": link["href"],
                "preco": limpar_preco(preco_atual.get_text())
            })

    return produtos
