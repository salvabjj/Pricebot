import os, asyncio
from playwright.async_api import async_playwright
from telegram import Bot

async def capturar_e_enviar():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)
    
    # URL de exemplo (Pode ser um termo de busca ou produto direto)
    url = "https://www.mercadolivre.com.br/ofertas" 

    async with async_playwright() as p:
        # Abre o navegador simula um usuário real
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        print(f"📸 Acessando: {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Tira o Print Screen de um elemento específico (ex: o primeiro produto)
        # Ou da tela cheia
        screenshot_path = "oferta.png"
        await page.screenshot(path=screenshot_path, full_page=False)
        
        # Envia para o Telegram
        with open(screenshot_path, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo, caption="🔥 *Oferta detectada via Captura de Tela!*")
        
        print("✅ Screenshot enviado com sucesso!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capturar_e_enviar())
