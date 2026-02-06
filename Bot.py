import os
import requestsimport os
import requests
from bs4 import BeautifulSoup
from telegram import Bot, ParseMode

# Pega as variáveis do ambiente (GitHub Secrets)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def buscar_oferta():import os, json, requests
from bs4 import BeautifulSoup
from telegram import Bot, ParseMode

# Configurações de Ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def carregar_json(nome_arquivo, valor_padrao):
    if os.path.exists(nome_arquivo):
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return valor_padrao

def salvar_json(nome_arquivo, dados):
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def buscar_oferta():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"}
    url = "https://www.mercadolivre.com.br/ofertas"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Seletores para o primeiro produto da grade de ofertas
        item = soup.find("p", class_="promotion-item__title")
        preco = soup.find("span", class_="andes-money-amount__fraction")
        link = soup.find("a", class_="promotion-item__link-container")

        if item and preco and link:
            return {
                "id": link['href'].split('MLB-')[1][:10] if 'MLB-' in link['href'] else link['href'],
                "titulo": item.text.strip(),
                "valor": preco.text.strip(),
                "url": link['href']
            }
    except Exception as e:
        print(f"Erro no scraping: {e}")
    return None

def main():
    bot = Bot(token=TOKEN)
    
    # Carrega arquivos que você já tem no Repo
    historico = carregar_json("History.json", [])
    afiliados = carregar_json("Affiliates.json", {})
    
    oferta = buscar_oferta()
    
    if oferta and oferta['id'] not in historico:
        # Adiciona sua tag de afiliado se existir no Affiliates.json
        tag = afiliados.get("mercadolivre", "")
        link_final = f"{oferta['url']}?af_id={tag}" if tag else oferta['url']
        
        msg = (
            f"🔥 *OFERTA NOVA*\n\n"
            f"📦 {oferta['titulo']}\n"
            f"💰 *R$ {oferta['valor']}*\n\n"
            f"🛒 [GARANTIR AGORA]({link_final})"
        )
        
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
        
        # Atualiza o histórico para não repetir
        historico.append(oferta['id'])
        salvar_json("History.json", historico[-100:]) # Mantém as últimas 100
        print("✅ Oferta postada e histórico atualizado!")
    else:
        print("⏭️ Nenhuma oferta nova para postar.")

if __name__ == "__main__":
    main()    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    url = "https://www.mercadolivre.com.br/ofertas"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Seletores atualizados para o Mercado Livre
        produto = soup.find("p", class_="promotion-item__title")
        preco = soup.find("span", class_="andes-money-amount__fraction")
        link = soup.find("a", class_="promotion-item__link-container")

        if produto and preco:
            return {
                "titulo": produto.text.strip(),
                "valor": preco.text.strip(),
                "url": link['href'] if link else url
            }
    except Exception as e:
        print(f"Erro no scraping: {e}")
    return None

def main():
    if not TOKEN or not CHAT_ID:
        print("❌ Erro: Variáveis TOKEN ou CHAT_ID não encontradas!")
        return

    bot = Bot(token=TOKEN)
    print("🤖 Iniciando monitoramento...")
    
    oferta = buscar_oferta()
    
    if oferta:
        msg = (
            f"🔥 *OFERTA ENCONTRADA*\n\n"
            f"📦 {oferta['titulo']}\n"
            f"💰 *R$ {oferta['valor']}*\n\n"
            f"🛒 [VER NO SITE]({oferta['url']})"
        )
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
        print("✅ Mensagem enviada!")
    else:
        print("0 ofertas capturadas nesta rodada.")

if __name__ == "__main__":
    main()from bs4 import BeautifulSoup
from telegram import Bot, ParseMode

def buscar_oferta():
    # Headers para o site não te banir
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    url = "https://www.mercadolivre.com.br/ofertas"
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Seletores simplificados
        item = soup.find("p", class_="promotion-item__title")
        preco = soup.find("span", class_="andes-money-amount__fraction")
        
        if item and preco:
            return f"🔥 *OFERTA:* {item.text}\n💰 *PREÇO:* R$ {preco.text}"
    except Exception as e:
        return f"Erro no scraping: {str(e)}"
    return None

if __name__ == "__main__":
    # Pega as variáveis que você cadastrou no GitHub Secrets
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    bot = Bot(token=token)
    texto = buscar_oferta()
    
    if texto:
        bot.send_message(chat_id=chat_id, text=texto, parse_mode=ParseMode.MARKDOWN)
        print("✅ Enviado!")
    else:
        print("❌ Nada encontrado.")    except Exception as e:
        print(f"Erro no scraping: {e}")
    return None

def main():
    bot = Bot(token=TOKEN)
    print("🤖 Iniciando monitoramento...")
    
    oferta = buscar_oferta()
    
    if oferta:
        msg = (
            f"🔥 *OFERTA ENCONTRADA*\n\n"
            f"📦 {oferta['titulo']}\n"
            f"💰 *R$ {oferta['valor']}*\n\n"
            f"🛒 [VER NO SITE]({oferta['url']})"
        )
        # Na v13.15, o envio é síncrono (sem await)
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
        print("✅ Mensagem enviada!")
    else:
        print("0 ofertas capturadas nesta rodada.")

if __name__ == "__main__":
    main()
