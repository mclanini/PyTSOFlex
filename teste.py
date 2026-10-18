
import os
import re



def read_contingencies(pasta):
    caminho = os.path.join(pasta, "RECTG.OUT")
    with open(caminho, "r", encoding="latin-1") as f:
        texto = f.read()
    texto = re.split(
        r"^\s*SUMARIO DE MONITORACAO",
        texto,
        maxsplit=1,
        flags=re.MULTILINE
    )[0]

    padrao = r"^\s*CONTINGENCIA\s+(\d+)\s+PRIORIDADE"
    partes = re.split(padrao, texto, flags=re.MULTILINE)
    contingencias = {}

    for i in range(1, len(partes), 2):
        numero = int(partes[i])
        conteudo = partes[i + 1]
        if numero not in contingencias:
            # Extrai os dados do circuito
            circuito = re.search(
                r"CIRCUITO\s+da\s+Barra\s+(\d+)\s+(\S+)\s+"
                r"p/\s+Barra\s+(\d+)\s+(\S+)",
                conteudo,
                flags=re.IGNORECASE
            )
            if circuito:
                barra_de, nome_de, barra_para, nome_para = circuito.groups()
                descricao = (
                    f"Contingência {numero} - "
                    f"Circuito da Barra {barra_de} ({nome_de}) "
                    f"p/ Barra {barra_para} ({nome_para})"
                )
            else:
                descricao = f"Contingência {numero}"
            contingencias[numero] = {
                "descricao": descricao,
                "texto": ""
            }
        contingencias[numero]["texto"] += conteudo + "\n"
    return contingencias

def check_convergence(contingencias):
    for numero, dados in contingencias.items():
        for line in dados["texto"].splitlines():
            linha = line.strip().upper()
            if linha == "CONVERGENCIA FINAL":
                break
            if "DIVERGENTE" in linha or "NAO CONVERGENTE" in linha:
                return False, numero, dados["descricao"]
    return True, None, None

def check_tensao(contingencias):
    mensagem = "Não foram encontradas violações de tensao entre as barras monitoradas."
    for numero, dados in contingencias.items():
        blocos = re.split(
            r"MONITORACAO DE TENSAO",
            dados["texto"]
        )
        for bloco in blocos[1:]:
            trecho = re.split(
                r"MONITORACAO DE|RELATORIO DE",
                bloco,
                maxsplit=1
            )[0]
            if mensagem not in trecho and trecho.strip():
                return True, numero, dados["descricao"]
    return False, None, None

def check_fluxo(contingencias):
    mensagem = "Não foram encontradas violações de fluxo entre os circuitos monitorados"
    for numero, dados in contingencias.items():
        blocos = re.split(
            r"MONITORACAO DE FLUXOS",
            dados["texto"]
        )
        for bloco in blocos[1:]:
            trecho = re.split(
                r"MONITORACAO DE|RELATORIO DE",
                bloco,
                maxsplit=1
            )[0]
            if mensagem not in trecho and trecho.strip():
                return True, numero, dados["descricao"]
    return False, None, None

def check_geracao(contingencias):
    for numero, dados in contingencias.items():
        if "MONITORACAO DE GERACAO" in dados["texto"]:
            return True, numero, dados["descricao"]
    return False, None, None


pasta = r"C:\Users\Usuario\Documents\Projeto_Regiao_Flexibilidade\PyTSOFlex"

contingencias = read_contingencies(pasta)

divergiu, num_div, desc_div = check_convergence(contingencias)

violou_tensao, num_tensao, desc_tensao = check_tensao(contingencias)

violou_fluxo, num_fluxo, desc_fluxo = check_fluxo(contingencias)

violou_geracao, num_geracao, desc_geracao = check_geracao(contingencias)

print("Convergência:", divergiu, num_div, desc_div)
print("Violou Tensão:", violou_tensao, num_tensao, desc_tensao)
print("Violou Fluxo:", violou_fluxo, num_fluxo, desc_fluxo)
print("Violou Geração:", violou_geracao, num_geracao, desc_geracao)
