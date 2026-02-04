# =========================
# ROBÔ DE OFERTAS - V1
# =========================

import time
import requests
from datetime import datetime

# ===== CONFIGURAÇÕES =====
TELEGRAM_TOKEN = "COLE_AQUI_O_TOKEN_DO_SEU_BOT"
TELEGRAM_CHAT_ID = "COLE_AQUI_O_ID_DO_CANAL"

# Textos por nicho
TEXTOS = {
    "moda": "👟🔥 OFERTA IMPERDÍVEL EM MODA!\nCorre que tá valendo a pena!",
    "eletronicos": "📱⚡ ELETRÔNICO COM PREÇO BAIXO!\nOferta que vende!",
    "casa": "🏠💥 OFERTA PRA CASA!\nPreço caiu agora!",
    "beleza": "💄✨ BELEZA COM DESCONTO!\nPromoção quente!",
}

# Simulação de ofertas (depois a gente conecta nas lojas)
OFERTAS = [
    {
        "nicho": "moda",
        "produto": "Tênis Nike",
        "preco": "R$ 199,90",
        "link": "SEU_LINK_DE_AFILIADO_AQUI"
    },
    {
        "nicho": "eletronicos",
        "produto": "Smartphone Samsung",
        "preco": "R$ 1.299,00",
        "link": "SEU_LINK_DE_AFILIADO_AQUI"
    }
]

# ===== FUNÇÕES =====
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def postar_ofertas():
    for oferta in OFERTAS:
        texto_base = TEXTOS.get(oferta["nicho"], "🔥 OFERTA!")
        mensagem = (
            f"{texto_base}\n\n"
            f"🛒 <b>{oferta['produto']}</b>\n"
            f"💰 {oferta['preco']}\n\n"
            f"👉 {oferta['link']}\n\n"
            f"⏰ {datetime.now().strftime('%d/%m %H:%M')}"
        )
        enviar_telegram(mensagem)
        time.sleep(5)

# ===== EXECUÇÃO =====
if __name__ == "__main__":
    print("🤖 Robô de ofertas rodando...")
    postar_ofertas()
