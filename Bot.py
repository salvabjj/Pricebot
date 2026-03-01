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
    print(response.status_code, response.text)

def run():
    all_products = []
    all_products += netshoes.capture()
    all_products += zattini.capture()

    for product in all_products:
        save_product(product)

if __name__ == "__main__":
    run()
