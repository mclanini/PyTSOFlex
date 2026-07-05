import subprocess
import time
import psutil
import os
import time
import math

def check_line_pq(lines, target_bar):
    #0         1         2         3         4         5         6         7          
    #01234567890123456789012345678901234567890123456789012345678901234567890123456789
    #(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
    idx_dbar = 0
    for i, linha in enumerate(lines):
        if linha.startswith("DBAR"):
            idx_dbar = i
        if i > idx_dbar and linha[0] != '(':
            if target_bar in linha[0:5].strip(): 
                idx = i
                Pl = float(linha[58:63])
                Ql = float(linha[63:68])
                break
    return idx, Pl, Ql

def execute_anarede(arquivo_pwf):   
    # Caminho completo do executável
    caminho_exe = r"C:\CEPEL\Anarede\V120001\\Anarede.exe"

    # Inicia o ANAREDE com o arquivo

    processo = subprocess.Popen([caminho_exe, arquivo_pwf])

    # Espera alguns segundos
    time.sleep(2)

    # Procura o processo certo para encerrar
    achou = False
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] == "ANAREDE.exe":
                print(f"Verificando processo PID={proc.info['pid']} EXE={proc.info.get('exe')}")
                if 'exe' in proc.info and proc.info['exe'] and os.path.samefile(proc.info['exe'], caminho_exe):
                    proc.kill()
                    print("✅ Processo ANAREDE encerrado com sucesso.")
                    achou = True
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, FileNotFoundError):
            continue
    if not achou:
        print("⚠️ Não foi possível localizar o processo do ANAREDE.")
    return achou

# def create_report(lines):
#     encontrou = False

#     i = 0
#     while i < len(lines) - 1:
#         if lines[i].strip() == "ULOG" and lines[i+1].strip() == "4":
#             encontrou = True
#             print('ENTREI AQUI')
#             # Garante que existe a linha seguinte
#             if i + 2 < len(lines):
#                 lines[i+2] = "RELAT_NEW.OUT\n"
#             else:
#                 lines.append("RELAT_NEW.OUT\n")
#             break
#         i += 1
#     # Se não encontrou, insere antes de FIM
#     if not encontrou:
#         bloco = [
#             "ULOG\n",
#             "4\n",
#             "RELAT_NEW.OUT\n",
#             "EXLF NEWT QLIM FILE\n",
#             "RELA RBAR RLIN FILE\n"
#         ]
#         for i, linha in enumerate(lines):
#             if linha.strip().startswith("FIM"):
#                 lines[i:i] = bloco  # insere antes do FIM
#                 break
#     return lines

def create_report(lines):
    encontrou = False
    # Faz um único strip para evitar múltiplos
    lines_strip = [line.strip() for line in lines]

    for i in range(len(lines_strip) - 1):
        if lines_strip[i] == "ULOG" and lines_strip[i + 1] == "4":
            encontrou = True
            # Se eu já tenho uma saída com ULOG 4 eu reescrevo para garantir o relatório correto
            bloco = [
                "RELAT_NEW.OUT\n",
                "EXLF NEWT QLIM FILE\n",
                "RELA RBAR RLIN FILE\n",
                "ULOG\n",
                "4\n",
                "REMON_NEW.OUT\n",
                "RELA RMON MOCT MOCF MOCG FILE\n",
                "ULOG\n",
                "4\n",
                "REMON_GER_NEW.OUT\n",
                "RELA RGEL\n"
            ]
            fim = i + 2 + len(bloco)
            if fim <= len(lines):
                lines[i + 2:fim] = bloco
            else:
                lines[i + 2:] = bloco
            break

    if not encontrou:
        # Se eu não encontrei ULOG 4, eu insiro o bloco completo antes do FIM
        bloco = [
            "ULOG\n",
            "4\n",
            "RELAT_NEW.OUT\n",
            "EXLF NEWT QLIM FILE\n",
            "RELA RBAR RLIN FILE\n",
            "ULOG\n",
            "4\n",
            "REMON_NEW.OUT\n",
            "RELA RMON MOCT MOCF MOCG FILE\n",
            "ULOG\n",
            "4\n",
            "REMON_GER_NEW.OUT\n",
            "RELA RGEL\n"
        ]

        for i, linha in enumerate(lines_strip):
            if linha == "FIM":
                lines[i:i] = bloco
                break
    return lines

def check_convergence():
    # Caminho do arquivo de entrada (.pwf)
    relatorio = "RELAT_NEW.OUT"
    convergiu = False
    with open(relatorio) as f: 
        lines = f.readlines()
    i = 0
    # Faz um único strip para evitar múltiplos
    lines_strip = [line.strip() for line in lines]
    while i <= len(lines_strip) - 1:
        if lines_strip[i] == "CONVERGENCIA FINAL":
            convergiu = True
            break
        i += 1
    return convergiu

def read_monitoring():
    # Caminho do arquivo de entrada (.pwf)
    relatorio = "REMON_NEW.OUT"
    with open(relatorio) as f: 
        lines = f.readlines()
    i = 0
    # Faz um único strip para evitar múltiplos
    lines_strip = [line.strip() for line in lines]
    return lines_strip

def check_tensao(lines_strip):
    violou_tensao = True
    i = 0
    while i <= len(lines_strip) - 1:
        if lines_strip[i] == "Não foram encontradas violações de tensao entre as barras monitoradas.":
            violou_tensao = False
            break
        i += 1
    return violou_tensao

def check_fluxo(lines_strip):
    violou_fluxo = True
    i = 0
    while i <= len(lines_strip) - 1:
        if lines_strip[i] == "Não foram encontradas violações de fluxo entre os circuitos monitorados":
            violou_fluxo = False
            break
        i += 1
    return violou_fluxo

def check_geracao():
    # Caminho do arquivo de entrada (.pwf)
    relatorio = "REMON_GER_NEW.OUT"
    if os.path.getsize(relatorio) == 0:
        violou_geracao = False
    else:
        violou_geracao = True
    return violou_geracao

def reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce_step):
    # Retorno pro último valor de Pl e Ql antes da divergência e diminuo o passo
    # Pl -= factor_P * (1 if math.cos(angulo) >= 0 else -1)
    # Ql -= factor_Q * (1 if math.sin(angulo) >= 0 else -1)
    Pl -= factor_P
    Ql -= factor_Q
    factor_P /= reduce_step
    factor_Q /= reduce_step
    minimal_step = True
    return Pl, Ql, factor_P, factor_Q, minimal_step