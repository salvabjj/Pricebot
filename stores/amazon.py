import requests
from bs4 import BeautifulSoup
from utils.parser import limpar_preco

def capturar():
    url = "https://www.amazon.com.br/deals"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    produtos = []

    for item in soup.select("a[href*='/dp/']")[:40]:
        link = item["href"]
        titulo = item.get_text(strip=True)

        if "/dp/" in link:
            produtos.append({
                "loja": "Amazon",
                "titulo": titulo,
                "link": "https://www.amazon.com.br" + link,
                "preco": None
            })

    return produtos
