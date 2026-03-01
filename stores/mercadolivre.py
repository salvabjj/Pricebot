import requests
from bs4 import BeautifulSoup
from utils.parser import limpar_preco

def capturar():
    url = "https://www.mercadolivre.com.br/ofertas"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    produtos = []

    for item in soup.select("li.ui-search-layout__item")[:40]:
        link = item.select_one("a")
        preco = item.select_one(".andes-money-amount__fraction")

        if link and preco:
            produtos.append({
                "loja": "Mercado Livre",
                "titulo": link.get_text(strip=True),
                "link": link["href"],
                "preco": limpar_preco(preco.get_text())
            })

    return produtos
