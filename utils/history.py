import json
import os

HISTORY_FILE = "History.json"

def carregar_historico():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def salvar_historico(historico):
    with open(HISTORY_FILE, "w") as f:
        json.dump(historico, f)

def ja_postado(link):
    historico = carregar_historico()
    return link in historico

def adicionar_historico(link):
    historico = carregar_historico()
    historico.append(link)
    salvar_historico(historico)
