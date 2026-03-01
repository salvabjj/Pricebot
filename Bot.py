Arquivo de fluxo de trabalho para esta execução.
.github/workflows/bot.yml em 3442c4d
das lojas importam amazon, mercadolivre, netshoes, zattini
de utils.telegram import enviar_oferta, enviar_relatorio
from utils.history import ja_postado, adicionar_historico

def executar() :
 Verifique a falha na linha 5 em .github/workflows/bot.yml


Ações do GitHub
/ .github/workflows/bot.yml
Arquivo de fluxo de trabalho inválido

You have an error in your yaml syntax on line 5

    todas = []
    todas += netshoes.capturar()
    todas += zattini.capturar()

    total = 0
    por_loja = {}

    para produto em todas :
        se não ja_postado(produto["link"]) :

            mensagem = f"""
🔥 {produto['titulo']}
💰 R$ {produto['preco']}
🏬 {produto['loja']}
🔗 {produto['link']}
" " "
            enviar_oferta(mensagem)
            adicionar_historico(produto[ " link"])

            total += 1
            loja = produto["loja"]
            por_loja[loja] = por_loja.get(loja, 0) + 1

    relatorio = f"📊 RELATÓRIO\n\nTotal : {total}\n\n"
    para loja, qtd em por_loja.items() :
        relatorio += f"{loja} : {qtd}\n"

    enviar_relatório(relatório)

se __name__ == "__main__" :
    executar()
