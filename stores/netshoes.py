import requests
from bs4 import BeautifulSoup

def clean_price(text):
    return float(
        text.replace("R$", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
    )

def capture():
    products = []
    url = "https://www.netshoes.com.br/ofertas"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select(".product-card")[:20]

    for card in cards:
        try:
            title = card.select_one(".product-name").get_text(strip=True)
            price = card.select_one(".product-price").get_text(strip=True)
            link = card.select_one("a")["href"]

            products.append({
                "title": title,
                "price": clean_price(price),
                "store": "Netshoes",
                "link": link,
                "posted": False
            })
        except:
            continue

    return products
