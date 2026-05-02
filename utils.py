import subprocess
import time
import psutil
import os

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

def create_report(lines):
    encontrou = False

    i = 0
    while i < len(lines) - 1:
        if lines[i].strip() == "ULOG" and lines[i+1].strip() == "4":
            encontrou = True
            print('ENTREI AQUI')
            # Garante que existe a linha seguinte
            if i + 2 < len(lines):
                lines[i+2] = "RELAT_NEW.OUT\n"
            else:
                lines.append("RELAT_NEW.OUT\n")
            break
        i += 1
    # Se não encontrou, insere antes de FIM
    if not encontrou:
        bloco = [
            "ULOG\n",
            "4\n",
            "RELAT_NEW.OUT\n",
            "EXLF NEWT QLIM FILE\n",
            "RELA RBAR RLIN FILE\n"
        ]
        for i, linha in enumerate(lines):
            if linha.strip().startswith("FIM"):
                lines[i:i] = bloco  # insere antes do FIM
                break
    return lines

def check_convergence():
    # Caminho do arquivo de entrada (.pwf)
    relatorio = "RELAT_NEW.OUT"
    convergiu = False
    with open(relatorio) as f: 
        lines = f.readlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip() == "CONVERGENCIA FINAL":
            convergiu = True
            break
        if lines[i].strip() == "SISTEMA CA DIVERGENTE":
            convergiu = False
            break
        i += 1
    return convergiu

# def alterar_pq_linha(linha, barra_alvo, P, Q):
#     if not linha.startswith("DBAR"):
#         return linha
#     #0         1         2         3         4         5         6         7          
#     #01234567890123456789012345678901234567890123456789012345678901234567890123456789
#     #(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
#     barra = int(linha[0:5])

#     if barra != barra_alvo:
#         return linha

#     Pl = float(linha[58:63]) #Carga Ativa
#     Ql= float(linha[63:68]) #Carga Reativa

#     Pl *= 1.01 #Aumenta a carga ativa em 1%
#     Ql *= 1.01 #Aumenta a carga reativa em 1%


#     COL_P_INI = 58
#     COL_P_FIM = 63
#     COL_Q_INI = 63
#     COL_Q_FIM = 68

#     nova_linha = (
#         linha[:COL_P_INI] +
#         f"{Pl:5.2f}" +
#         f"{Ql:5.2f}" +
#         linha[COL_Q_FIM:]
#     )
#     return nova_linha