import os
import requests
from stores import netshoes, zattini

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def save_product(product):
    url = f"{SUPABASE_URL}/rest/v1/products"
    response = requests.post(url, headers=HEADERS, json=product)
    print("INSERT STATUS:", response.status_code)
    print("INSERT RESPONSE:", response.text)

def run():
    print("BOT STARTED")

    all_products = []
    net = netshoes.capture()
    zat = zattini.capture()

    print("NETSHOES FOUND:", len(net))
    print("ZATTINI FOUND:", len(zat))

    all_products += net
    all_products += zat

    print("TOTAL PRODUCTS:", len(all_products))

    for product in all_products:
        print("SENDING:", product["title"])
        save_product(product)

if __name__ == "__main__":
    run()
