import requests
from bs4 import BeautifulSoup

def limpar_preco(texto):
    return texto.replace("R$", "").replace(".", "").replace(",", ".").strip()

def capturar():
    produtos = []
    url = "https://www.zattini.com.br/ofertas"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select(".product-card")[:20]

    for card in cards:
        try:
            titulo = card.select_one(".product-name").get_text(strip=True)
            preco = card.select_one(".product-price").get_text(strip=True)
            link = card.select_one("a")["href"]

            produtos.append({
                "titulo": titulo,
                "preco": float(limpar_preco(preco)),
                "loja": "Zattini",
                "link": link
            })
        except:
            continue

    return produtos
