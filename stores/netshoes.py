import requests
from bs4 import BeautifulSoup
from utils.parser import limpar_preco

def capturar():
    url = "https://www.netshoes.com.br/tenis"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    produtos = []

    for item in soup.select("[data-testid='product-card']")[:40]:
        link = item.select_one("a")
        preco = item.select_one("[data-testid='price-current']")

        if link and preco:
            produtos.append({
                "loja": "Netshoes",
                "titulo": link.get_text(strip=True),
                "link": link["href"],
                "preco": limpar_preco(preco.get_text())
            })

    return produtos
