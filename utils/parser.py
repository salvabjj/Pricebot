import re

def limpar_preco(texto):
    if not texto:
        return None
    texto = texto.replace('.', '').replace(',', '.')
    match = re.search(r'\d+(\.\d+)?', texto)
    return float(match.group()) if match else None
