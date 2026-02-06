import os
import json
import requests
from bs4 import BeautifulSoup
from telegram import Bot, ParseMode

# Variaveis do GitHub Secrets
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def abrir_memoria(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return padrao
    return padrao

def buscar_produto():
    url = "https://www.mercadolivre.com.br/ofertas"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Seletores de 2026 para o Mercado Livre
        item = soup.find("p", class_="promotion-item__title")
        preco = soup.find("span", class_="andes-money-amount__fraction")
        link = soup.find("a", class_="promotion-item__link-container")

        if item and preco and link:
            return {
                "id": link['href'][:50], # Usa o começo do link como ID
                "nome": item.text.strip(),
                "preco": preco.text.strip(),
                "url": link['href']
            }
    except Exception as e:
        print(f"Falha no scraping: {e}")
    return None

def main():
    if not TOKEN or not CHAT_ID:
        print("❌ Erro: Secrets do Telegram não configurados!")
        return

    bot = Bot(token=TOKEN)
    historico = abrir_memoria("History.json", [])
    afiliados = abrir_memoria("Affiliates.json", {})

    produto = buscar_produto()

    if produto and produto['id'] not in historico:
        # Pega sua tag do Affiliates.json
        tag = afiliados.get("mercadolivre", "salvabjj-20") 
        link_final = f"{produto['url']}?tag={tag}"
        
        msg = (
            f"🔥 *OFERTA ENCONTRADA*\n\n"
            f"📦 {produto['nome']}\n"
            f"💰 *R$ {produto['preco']}*\n\n"
            f"🛒 [COMPRAR AGORA]({link_final})"
        )
        
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
        
        # Salva para não repetir
        historico.append(produto['id'])
        with open("History.json", "w", encoding="utf-8") as f:
            json.dump(historico[-50:], f) # Guarda as últimas 50
        print("✅ Postado!")
    else:
        print("⏭️ Nenhuma novidade ou produto já postado.")

if __name__ == "__main__":
    main()                "valor": preco.text.strip(),
                "url": link['href']
            }
    except Exception as e:
        print(f"Erro no scraping: {e}")
    return None

def main():
    if not TOKEN or not CHAT_ID:
        print("ERRO: Configure o TOKEN e CHAT_ID no GitHub Secrets!")
        return

    bot = Bot(token=TOKEN)
    
    # Busca dados nos arquivos que voce ja tem no GitHub
    historico = gerenciar_json("History.json", [])
    afiliados = gerenciar_json("Affiliates.json", {})
    
    oferta = buscar_oferta()
    
    if oferta and oferta['id'] not in historico:
        # Pega o ID de afiliado do seu Affiliates.json
        tag = afiliados.get("mercadolivre", "")
        url_final = f"{oferta['url']}?pdp_filters=category%3A{tag}" if tag else oferta['url']
        
        msg = (
            f"🔥 *OFERTA ENCONTRADA*\n\n"
            f"📦 {oferta['titulo']}\n"
            f"💰 *R$ {oferta['valor']}*\n\n"
            f"🛒 [COMPRAR AGORA]({url_final})"
        )
        
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
        
        # Salva no histórico para não repetir
        historico.append(oferta['id'])
        with open("History.json", "w", encoding="utf-8") as f:
            json.dump(historico[-50:], f) # Guarda só as últimas 50
        print("✅ Postado com sucesso!")
    else:
        print("0 ofertas novas encontradas.")

if __name__ == "__main__":
    main()
