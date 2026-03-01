from stores import netshoes, zattini
from utils.telegram import enviar_oferta, enviar_relatorio
from utils.history import ja_postado, adicionar_historico


LOJAS = [
    netshoes.capturar,
    zattini.capturar
]


def executar():
    todas = []

    for capturar in LOJAS:
        try:
            produtos = capturar()
            todas += produtos
        except Exception as e:
            print(f"Erro na loja: {e}")

    total = 0
    por_loja = {}

    for produto in todas:
        if not ja_postado(produto["link"]):

            mensagem = f"""🔥 {produto['titulo']}
💰 R$ {produto['preco']}
🏬 {produto['loja']}
🔗 {produto['link']}"""

            enviar_oferta(mensagem)
            adicionar_historico(produto["link"])

            total += 1
            loja = produto["loja"]
            por_loja[loja] = por_loja.get(loja, 0) + 1

    relatorio = f"📊 RELATÓRIO\n\nTotal: {total}\n\n"

    for loja, qtd in por_loja.items():
        relatorio += f"{loja}: {qtd}\n"

    enviar_relatorio(relatorio)


if __name__ == "__main__":
    executar()