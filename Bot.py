import os
import requests
from lojas import netshoes, zattini

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def salvar_produto(produto):
    url = f"{SUPABASE_URL}/rest/v1/products"
    response = requests.post(url, headers=HEADERS, json=produto)
    print(response.status_code, response.text)

def executar():
    todas = []
    todas += netshoes.capturar()
    todas += zattini.capturar()

    for produto in todas:
        salvar_produto(produto)

if __name__ == "__main__":
    executar()
