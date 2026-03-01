import os
import random
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from supabase import create_client
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------
# SALVAR OU ATUALIZAR PRODUTO
# -----------------------------------

def save_or_update(loja, titulo, preco, link, categoria):

    existing = supabase.table("products") \
        .select("*") \
        .eq("link", link) \
        .execute()

    now = datetime.utcnow().isoformat()

    if not existing.data:
        # NOVO PRODUTO
        supabase.table("products").insert({
            "loja": loja,
            "titulo": titulo,
            "preco": preco,
            "preco_antigo": preco,
            "menor_preco": preco,
            "link": link,
            "categoria": categoria,
            "score": 0,
            "queda_recente": False
        }).execute()

        print("NOVO:", titulo)
        return

    produto = existing.data[0]

    preco_antigo = produto["preco"]
    menor_preco = produto["menor_preco"]

    # SE PREÇO CAIU
    if preco < preco_antigo:

        novo_menor = preco if preco < menor_preco else menor_preco

        supabase.table("products").update({
            "preco_antigo": preco_antigo,
            "preco": preco,
            "menor_preco": novo_menor,
            "queda_recente": True,
            "atualizado_em": now
        }).eq("link", link).execute()

        print("QUEDA DETECTADA:", titulo)
        return

    # SE PREÇO SUBIU
    if preco > preco_antigo:

        supabase.table("products").update({
            "preco_antigo": preco_antigo,
            "preco": preco,
            "queda_recente": False,
            "atualizado_em": now
        }).eq("link", link).execute()

        print("PREÇO SUBIU:", titulo)
        return

    print("SEM ALTERAÇÃO:", titulo)

# -----------------------------------
# EXTRAIR PREÇO
# -----------------------------------

def extract_price(text):
    import re
    match = re.search(r'R\$ ?([\d\.]+,\d{2})', text)
    if not match:
        return None
    valor = match.group(1).replace(".", "").replace(",", ".")
    return float(valor)

# -----------------------------------
# NETSHOES / ZATTINI (REQUESTS)
# -----------------------------------

def scrape_requests(base_url, termo, loja, categoria):

    headers = {"User-Agent": "Mozilla/5.0"}
    url = base_url + termo.replace(" ", "+")
    r = requests.get(url, headers=headers, timeout=20)

    soup = BeautifulSoup(r.text, "html.parser")

    links = [a["href"] for a in soup.find_all("a", href=True)
             if "/p/" in a["href"]]

    random.shuffle(links)

    for link in links[:5]:

        full = link if link.startswith("http") else base_url.split("/busca")[0] + link

        page = requests.get(full, headers=headers, timeout=20)
        price = extract_price(page.text)

        if not price:
            continue

        save_or_update(loja, termo, price, full, categoria)

# -----------------------------------
# AMAZON / MERCADO LIVRE (PLAYWRIGHT)
# -----------------------------------

def scrape_playwright(search_url, termo, loja, categoria):

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(search_url + termo.replace(" ", "+"), timeout=60000)
        page.wait_for_timeout(5000)

        links = page.locator("a").all()

        count = 0

        for a in links:

            href = a.get_attribute("href")
            if not href:
                continue

            if "/dp/" in href or "MLB" in href:

                full = href if href.startswith("http") else search_url + href

                page.goto(full)
                page.wait_for_timeout(3000)

                price = extract_price(page.content())

                if not price:
                    continue

                save_or_update(loja, termo, price, full, categoria)

                count += 1
                if count >= 3:
                    break

        browser.close()

# -----------------------------------
# MAIN
# -----------------------------------

def main():

    termos = [
        ("tenis adidas", "moda"),
        ("iphone 15", "eletronicos"),
        ("whey protein", "fitness"),
        ("smartwatch", "eletronicos"),
        ("luva de boxe", "esportes")
    ]

    for termo, categoria in termos:

        scrape_requests(
            "https://www.netshoes.com.br/busca?q=",
            termo,
            "netshoes",
            categoria
        )

        scrape_requests(
            "https://www.zattini.com.br/busca?q=",
            termo,
            "zattini",
            categoria
        )

        scrape_playwright(
            "https://www.amazon.com.br/s?k=",
            termo,
            "amazon",
            categoria
        )

        scrape_playwright(
            "https://lista.mercadolivre.com.br/",
            termo,
            "mercadolivre",
            categoria
        )

if __name__ == "__main__":
    main()
