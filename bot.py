import os
import json
import time
import random
import requests
from datetime import datetime

# ==========================
# CONFIGURAÇÕES
# ==========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HISTORY_FILE = "history.json"
POSTS_PER_RUN = 3  # mínimo garantido
TIME_BETWEEN_POSTS = 3  # segundos

AFFILIATES = {
    "amazon": "https://www.amazon.com.br/?tag=salvablessjj-20",
    "shopee": "https://shopee.com.br",
    "mercadolivre": "https://www.mercadolivre.com.br",
    "netshoes": "https://www.netshoes.com.br/afiliado/rWODdSNWJGM",
    "zattini": "https://www.zattini.com.br"
}

# ==========================
# CATEGORIAS
# ==========================
CATEGORIES = [
    {"nome": "Moda Masculina", "site": "amazon"},
    {"nome": "Moda Feminina", "site": "zattini"},
    {"nome": "Moda Infantil", "site": "netshoes"},
    {"nome": "Eletrônicos", "site": "mercadolivre"},
    {"nome": "Esportes", "site": "shopee"},
    {"nome": "Casa", "site": "amazon"},
    {"nome": "Suplementos", "site": "amazon"}
]

# ==========================
# HISTORY
# ==========================
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# ==========================
# TELEGRAM
# ==========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()

# ==========================
# GERADOR DE POST
# ==========================
def build_post(category):
    site = category.get("site", "amazon")
    link = AFFILIATES.get(site, AFFILIATES["amazon"])

    return f"""
🔥 *CONFIRA AS OFERTAS DO DIA!*

👕 *{category['nome']}*
Selecionamos produtos com ótimo custo-benefício.

🛒 Confira agora:
{link}
"""

# ==========================
# EXECUÇÃO PRINCIPAL
# ==========================
def main():
    history = load_history()
    sent = 0

    random.shuffle(CATEGORIES)

    for cat in CATEGORIES:
        if sent >= POSTS_PER_RUN:
            break

        try:
            message = build_post(cat)
            send_telegram(message)

            history.append({
                "categoria": cat["nome"],
                "site": cat.get("site", "amazon"),
                "data": datetime.utcnow().isoformat()
            })

            sent += 1
            time.sleep(TIME_BETWEEN_POSTS)

        except Exception as e:
            print(f"Erro ao postar {cat['nome']}: {e}")

    save_history(history)

    if sent == 0:
        send_telegram("⚠️ Nenhuma oferta enviada nesta execução.")

# ==========================
if __name__ == "__main__":
    main()