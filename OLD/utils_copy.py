import shutil
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

def criar_arquivo_dat(caminho_pwf, caminho_pasta, angulo):
    caminho_dat = os.path.join(caminho_pasta, f"arquivo_{angulo}.pwf")
    # o arquivo .pwf tem as linhas 3 e 7 como variáveis, sendo criado para cada ângulo.
    linhas = [
        "ULOG\n",
        "1\n",
        f"{caminho_pwf}\n",
        "EXLF NEWT QLIM\n",
        "ULOG\n",
        "2\n",
        f"{caminho_pasta}\TESTE_{angulo}.SAV\n",
        "ARQV INIC NOVO\n",
        "SIM\n",
        "TITU\n",
        "Original\n",
        "ARQV GRAV\n",
        "01\n",
        # "DOSC\n",
        # "TASKKILL /T /F /IM ANAREDE.EXE\n",
        # "99999\n",
        "FIM"
    ]
    with open(caminho_dat, "w", encoding="utf-8") as f:
        f.writelines(linhas)
    return caminho_dat

def criar_arquivo2_dat(iteracao, caminho_pasta, angulo, new_line):
    caminho_dat = os.path.join(caminho_pasta, f"arquivo2_{angulo}.pwf")
    linhas = [
        "ULOG\n",
        "2\n",
        f"{caminho_pasta}\TESTE_{angulo}.SAV\n",
        "ARQV REST\n",
        f"{iteracao:02d}\n",
        "DOPC\n",
        "FILE L\n",
        "99999\n",
        "DOSC\n",
        f"DEL {caminho_pasta}\*.out\n",
        "99999\n",
        "DBAR IMPR\n",
        f"(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10\n",
        f"{new_line}\n",
        "99999\n",
        "ULOG\n",
        "4\n",
        f"{caminho_pasta}\RELAT_NEW.OUT\n",
        "EXLF NEWT QLIM FILE\n",
        "RELA RBAR RLIN FILE\n",
        "TITU\n",
        f"Direcao_{angulo}_caso_{iteracao}\n",
        "ARQV GRAV\n",
        f"{iteracao+1:02d}\n",
        "ULOG\n",
        "4\n",
        f"{caminho_pasta}\REMON_NEW.OUT\n",
        "RELA RMON MOCT MOCF MOCG FILE\n",
        "ULOG\n",
        "4\n",
        f"{caminho_pasta}\REMON_GER_NEW.OUT\n",
        "RELA RGEL\n",
        # "DOSC\n",
        # "TASKKILL /T /F /IM ANAREDE.EXE\n",
        # "99999\n",
        "FIM"
    ]
    with open(caminho_dat, "w", encoding="utf-8") as f:
        f.writelines(linhas)
    return caminho_dat

def execute_anarede(arquivo):   
    # Caminho completo do executável
    caminho_exe = r"C:\CEPEL\Anarede\V130001\\ANAREDE.exe"

    # Inicia o ANAREDE com o arquivo
    processo = subprocess.Popen([caminho_exe, arquivo])
    # Espera alguns segundos
    time.sleep(3)

def create_report(lines, caminho_pasta):
    encontrou = False
    # Faz um único strip para evitar múltiplos
    lines_strip = [line.strip() for line in lines]
    for i in range(len(lines_strip) - 1):
        if lines_strip[i] == "ULOG" and lines_strip[i + 1] == "4":
            encontrou = True
            # Se eu já tenho uma saída com ULOG 4 eu reescrevo para garantir o relatório correto
            bloco = [
                f"{caminho_pasta}\RELAT_NEW.OUT\n",
                "EXLF NEWT QLIM FILE\n",
                "RELA RBAR RLIN FILE\n",
                "ULOG\n",
                "4\n",
                f"{caminho_pasta}\REMON_NEW.OUT\n",
                "RELA RMON MOCT MOCF MOCG FILE\n",
                "ULOG\n",
                "4\n",
                f"{caminho_pasta}\REMON_GER_NEW.OUT\n",
                "RELA RGEL\n",
            ]
            inicio = i + 2
            fim = inicio
            while fim < len(lines_strip) and lines_strip[fim] != "FIM":
                fim += 1
            lines[inicio:fim] = bloco
            break
    if not encontrou:
        # Se eu não encontrei ULOG 4, eu insiro o bloco completo antes do FIM
        bloco = [
            "ULOG\n",
            "4\n",
            f"{caminho_pasta}\RELAT_NEW.OUT\n",
            "EXLF NEWT QLIM FILE\n",
            "RELA RBAR RLIN FILE\n",
            "ULOG\n",
            "4\n",
            f"{caminho_pasta}\REMON_NEW.OUT\n",
            "RELA RMON MOCT MOCF MOCG FILE\n",
            "ULOG\n",
            "4\n",
            f"{caminho_pasta}\REMON_GER_NEW.OUT\n",
            "RELA RGEL\n",
        ]
        for i, linha in enumerate(lines_strip):
            if linha == "FIM":
                lines[i:i] = bloco
                break
    return lines

def check_convergence(pasta):
    # Caminho do arquivo de entrada (.pwf)
    relatorio = os.path.join(pasta, "RELAT_NEW.OUT")
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

def read_monitoring(pasta):
    # Caminho do arquivo de entrada (.pwf)
    relatorio = os.path.join(pasta, "REMON_NEW.OUT")
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

def check_geracao(pasta):
    # Caminho do arquivo de entrada (.pwf)
    relatorio = os.path.join(pasta, "REMON_GER_NEW.OUT")
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

def processa_angulo(angulo, Pl_original, Ql_original, arquivo_pwf, factor, reduce, lines, target_line):
#   Inicialização das variáveis de controle
    converged = True
    violou_tensao = False
    violou_fluxo = False
    violou_geracao = False
#   Inicialização das variáveis de controle
    first_divergence = False
    first_tensao = False
    first_fluxo = False
    first_geracao = False
#   Inicialização das variáveis de controle
    minimal_step = False
#   Inicialização das variáveis de controle
    observacao = ''
    plot_list = []
    exit_list = []
    iteracao = 0
    Pl = Pl_original
    Ql = Ql_original
    Pl_old, Ql_old = 0, 0

    exit_list.append({
        "Ângulo": "-",
        "Iteracao": iteracao,
        "Característica": "Original",
        "PL": f"{Pl:5.2f}"[:5],
        "QL": f"{Ql:5.2f}"[:5],
        "Violação de Tensão": "Sim" if violou_tensao else "Não",
        "Violação de Fluxo": "Sim" if violou_fluxo else "Não",
        "Violação de Geração": "Sim" if violou_geracao else "Não",
        "Convergiu": True,
    })
    plot_list.append({
        "Ângulo": "-",
        "Característica": "Original",
        "PL": f"{Pl:5.2f}"[:5],
        "QL": f"{Ql:5.2f}"[:5],
        "Violação de Tensão": "Sim" if violou_tensao else "Não",
        "Violação de Fluxo": "Sim" if violou_fluxo else "Não",
        "Violação de Geração": "Sim" if violou_geracao else "Não",
        "Convergiu": "Sim" if converged else "Não",
    })

#   INICIA O PROCESSO DE ANÁLISE PARA O ÂNGULO ESPECÍFICO
    angulo_graus = int(round(math.degrees(angulo)))
    # Cria pasta base do projeto
    pasta_base = r"C:\PyTSOFlex"
    # Cria a pasta do ângulo
    pasta = os.path.join(pasta_base, str(angulo_graus))
    # Se já existir, remove tudo
    if os.path.exists(pasta):
        shutil.rmtree(pasta)
    # Cria novamente a pasta vazia
    os.makedirs(pasta)
    # Caminho completo
    caminho_pasta = os.path.abspath(pasta)

    # Modifica linha para salvar relatório com nome diferente caso exista o ULOG e não sobrepor o original
    lines = create_report(lines, caminho_pasta)
    #Reescreve arquivo com as saídas para os relatórios no diretório do ângulo
    nome, extensao = os.path.splitext(os.path.basename(arquivo_pwf))
    pwf_final = os.path.join(caminho_pasta, f"{nome}_{angulo_graus}{extensao}")
    with open(pwf_final, "w") as f:
            f.writelines(lines)

    # Cria o arquivo.pwf dentro da pasta (arquivo base para leitura do PWF e criação do .sav)
    arquivo_dat = criar_arquivo_dat(
        caminho_pwf=pwf_final,
        caminho_pasta=caminho_pasta,
        angulo=angulo_graus
    )
    # Calcula o fator de aumento para a potência ativa daquele angulo
    factor_P = factor * math.cos(angulo)
    # Calcula o fator de aumento para a potência reativa daquele angulo
    factor_Q = factor * math.sin(angulo)
    while converged == True:
        # Chamar o ANAREDE encapsulado para rodar o arquivo modificado
        execute_anarede(arquivo_dat)
        # # Espera alguns segundos
        time.sleep(2)
        # Verifica criação do arquivo de relatório para garantir que o ANAREDE rodou
        executed = (
            os.path.exists(os.path.join(caminho_pasta, "RELAT_NEW.OUT"))
        )
        if not executed:
            print(f"❌ Falha ao executar o ANAREDE ou gerar um dos relatórios. ANGULO: {angulo_graus}° | CASO: {iteracao}")
            break
        else:
            print(f"✅ ANAREDE executado e relatório gerado com sucesso. ANGULO: {angulo_graus}° | CASO: {iteracao}")
            # Lê o relatório para verificar convergência
            converged = check_convergence(pasta)
            if converged:
                print(f"🔄 Convergência atingida, violações serão analisadas. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                lines_monitoring = read_monitoring(pasta)
                # ---------------- ANÁLISE DE TENSÃO ----------------
                # Se ainda não violou tensão entro no IF e continuo verificando a cada iteração
                if not violou_tensao:
                    # Verifico se nessa condição houve violação de tensão
                    violou_tensao = check_tensao(lines_monitoring)
                    if violou_tensao:
                        print(f"✅ Tensão violou. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                        # Se eu violei tensão e já tive a primeira violação DE TENSÃO, 
                        # então a análise de tensão acaba
                        if first_tensao:
                            print(f"✅ Ponto de violação de tensão encontrado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                            violou_tensao = True
                            # Flag de análise de pré violação volta a ser False
                            violou_tensao = False
                            # Se eu não estiver verificando nenhuma outra violação,
                            # posso retornar o passo para o normal
                            if not first_fluxo and not first_geracao and not first_divergence and minimal_step:
                                factor_P *= reduce
                                factor_Q *= reduce
                                minimal_step = False
                            plot_list.append({
                                "Ângulo": f"{math.degrees(angulo):.0f}°",
                                "Característica": "Modificado",
                                "PL": f"{Pl:5.2f}"[:5],
                                "QL": f"{Ql:5.2f}"[:5],
                                "Violação de Tensão": "Sim"
                            })
                        else:
                            # Se violou e ainda não tive nehuma primeira violação (qualquer uma), 
                            # eu reduzo o passo
                            if not minimal_step:
                                first_tensao = True
                                print(f"✅ Primeira violação de tensão atingida, passo será reduzido. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                                violou_tensao = False
                                # Retorno pro último valor de Pl e Ql antes da divergência 
                                # e diminuo o passo
                                Pl_old, Ql_old = Pl, Ql
                                Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                            # Se violou tensão e já tive alguma violação (qualquer uma) não reduzo o passo
                            else:
                                first_tensao = True
                                print(f"✅ Primeira violação de tensão atingida. Passo já está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                                violou_tensao = False
                            # Acrescento observação no ponto de primeira violação de tensão
                            if observacao == '':
                                observacao = "Ponto da primeira violação de tensão"
                            else:
                                observacao += " | Ponto da primeira violação de tensão" 
                # ---------------- ANÁLISE DE FLUXO ----------------
                # Se ainda não violou fluxo entro no IF e continuo verificando a cada iteração
                if not violou_fluxo:
                    # Verifico se nessa condição houve violação de fluxo
                    violou_fluxo = check_fluxo(lines_monitoring)
                    if violou_fluxo:
                        print(f"✅ Fluxo violou. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                        print(lines_monitoring)
                        # Se eu violei fluxo e já tive a primeira violação DE FLUXO, 
                        # então a análise de fluxo acaba
                        if first_fluxo:
                            print(f"✅ Ponto de violação de fluxo encontrado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                            violou_fluxo = True
                            # Flag de análise de pré violação volta a ser False
                            first_fluxo = False
                            # Se eu não estiver verificando nenhuma outra violação,
                            # posso retornar o passo para o normal
                            if not first_tensao and not first_geracao and not first_divergence and minimal_step:
                                factor_P *= reduce
                                factor_Q *= reduce
                                minimal_step = False
                            plot_list.append({
                                "Ângulo": f"{math.degrees(angulo):.0f}°",
                                "Característica": "Modificado",
                                "PL": f"{Pl:5.2f}"[:5],
                                "QL": f"{Ql:5.2f}"[:5],
                                "Violação de Fluxo": "Sim"
                            })
                        else:
                            # Se violou e ainda não tive nehuma primeira violação (qualquer uma), 
                            # eu reduzo o passo
                            if not minimal_step:
                                first_fluxo = True
                                print(f"✅ Primeira violação de fluxo atingida, passo será reduzido. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                                violou_fluxo = False
                                # Retorno pro último valor de Pl e Ql antes da divergência 
                                # e diminuo o passo
                                Pl_old, Ql_old = Pl, Ql
                                Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                            # Se violou fluxo e já tive alguma violação (qualquer uma) não reduzo o passo
                            else:
                                first_fluxo = True
                                print(f"✅ Primeira violação de fluxo atingida. Passo já está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                                violou_fluxo = False
                            # Acrescento observação no ponto de primeira violação de fluxo
                            if observacao == '':
                                observacao = "Ponto da primeira violação de fluxo"
                            else:
                                observacao += " | Ponto da primeira violação de fluxo" 
                # ---------------- ANÁLISE DE GERAÇÃO ----------------
                # Se ainda não violou geração entro no IF e continuo verificando a cada iteração
                if not violou_geracao:
                    # Verifico se nessa condição houve violação de geração
                    violou_geracao = check_geracao(pasta)
                    if violou_geracao:
                        print(f"✅ Geração violou. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                        # Se eu violei geração e já tive a primeira violação DE GERAÇÃO, 
                        # então a análise de geração acaba
                        if first_geracao:
                            print(f"✅ Ponto de violação de geração encontrado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                            violou_geracao = True
                            # Flag de análise de pré violação volta a ser False
                            first_geracao = False
                            # Se eu não estiver verificando nenhuma outra violação,
                            # posso retornar o passo para o normal
                            if not first_fluxo and not first_tensao and not first_divergence and minimal_step:
                                factor_P *= reduce
                                factor_Q *= reduce
                                minimal_step = False
                            plot_list.append({
                                "Ângulo": f"{math.degrees(angulo):.0f}°",
                                "Característica": "Modificado",
                                "PL": f"{Pl:5.2f}"[:5],
                                "QL": f"{Ql:5.2f}"[:5],
                                "Violação de Geração": "Sim"
                            })
                        else:
                            # Se violou e ainda não tive nehuma primeira violação (qualquer uma), 
                            # eu reduzo o passo
                            if not minimal_step:
                                first_geracao = True
                                print(f"✅ Primeira violação de geração atingida, passo será reduzido. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                                violou_geracao = False
                                # Retorno pro último valor de Pl e Ql antes da divergência e 
                                # diminuo o passo
                                Pl_old, Ql_old = Pl, Ql
                                Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                            # Se violou geração e já tive alguma violação (qualquer uma) não reduzo o passo
                            else:
                                first_geracao = True
                                print(f"✅ Primeira violação de geração atingida. Passo já está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                                violou_geracao = False
                            # Acrescento observação no ponto de primeira violação de geração
                            if observacao == '':
                                observacao = "Ponto da primeira violação de geração"
                            else:
                                observacao += " | Ponto da primeira violação de geração"
            # ---------------- ANÁLISE DE CONVERGÊNCIA ----------------
            # Se já divergiu eu não verifico violação
            else:
                # Se já teve a primeira divergência, encerra o processo.
                if first_divergence:
                    print(f"✅ Ponto de divergência encontrado, processo será finalizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                    iteracao += 1
                    exit_list.append({
                        "Ângulo": f"{math.degrees(angulo):.0f}°",
                        "Iteracao": iteracao,
                        "Característica": "Modificado",
                        "PL": f"{Pl:5.2f}"[:5],
                        "QL": f"{Ql:5.2f}"[:5],
                        "Convergiu": converged,
                        "Violação de Tensão": "Sim" if violou_tensao else "Não",
                        "Violação de Fluxo": "Sim" if violou_fluxo else "Não",
                        "Violação de Geração": "Sim" if violou_geracao else "Não"
                    })
                    plot_list.append({
                                "Ângulo": f"{math.degrees(angulo):.0f}°",
                                "Característica": "Modificado",
                                "PL": f"{Pl:5.2f}"[:5],
                                "QL": f"{Ql:5.2f}"[:5],
                                "Convergiu": "Não"
                    })
                     # CASO O ANAREDE TENHA DADO ERRO DEVIDO A NÃO CONVERGÊNCIA, ENCERRA o PROCESSO DO ANAREDE
                    # DE FORMA FORÇADA PARA EVITAR QUE O ANAREDE FIQUE ABERTO E IMPEDINDO A PRÓXIMA EXECUÇÃO
                    # Caminho completo do executável
                    caminho_exe = r"C:\CEPEL\Anarede\V130001\\ANAREDE.exe"
                    for proc in psutil.process_iter(['pid', 'name', 'exe']):
                        try:
                            # Verifica se o processo do ANAREDE ainda está em execução e se sim finaliza.
                            if proc.info['name'] == "ANAREDE.exe":
                                if 'exe' in proc.info and proc.info['exe'] and os.path.samefile(proc.info['exe'], caminho_exe):
                                    proc.kill()
                                    break
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, FileNotFoundError):
                            continue
                    break
                iteracao -= 1
                # Acrescento observação no ponto de primeira violação de geração
                if observacao == '':
                    observacao = "Ponto da primeira divergência"
                else:
                    observacao += " | Ponto da primeira divergência"
                # Se divergiu e ainda não tive nehuma primeira violação, eu reduzo o passo
                if not minimal_step:
                    first_divergence = True
                    print(f"✅ Primeira divergência atingida, passo será reduzido. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                    converged = True
                    # Retorno pro último valor de Pl e Ql antes da divergência e diminuo o passo
                    Pl_old, Ql_old = Pl, Ql
                    Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                # Se divergiu e já tive alguma divergência, não reduzo o passo
                else:
                    first_divergence = True
                    print(f"✅ Primeira divergência atingida. Passo já está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                    converged = True
        iteracao += 1
        exit_list.append({
            "Ângulo": f"{math.degrees(angulo):.0f}°",
            "Iteracao": iteracao,
            "Característica": "Modificado",
            "PL": f"{Pl:5.2f}"[:5] if Pl_old == 0 else f"{Pl_old:5.2f}"[:5],
            "QL": f"{Ql:5.2f}"[:5] if Ql_old == 0 else f"{Ql_old:5.2f}"[:5],
            "Convergiu": converged,
            "Violação de Tensão": "Sim" if violou_tensao else "Não",
            "Violação de Fluxo": "Sim" if violou_fluxo else "Não",
            "Violação de Geração": "Sim" if violou_geracao else "Não",
            "Observação": observacao
        })
        observacao = ''
        Pl_old, Ql_old = 0, 0

        Pl += factor_P
        Ql += factor_Q
        #Atualiza linha
        #0         1         2         3         4         5         6         7          
        #01234567890123456789012345678901234567890123456789012345678901234567890123456789
        #(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
        new_line = (
            lines[target_line][:5] +
            "M" +
            " " * 52 +
            f"{Pl:5.2f}"[:5] +
            f"{Ql:5.2f}"[:5]
        )
        arquivo_dat = criar_arquivo2_dat(
            iteracao=iteracao,
            caminho_pasta=caminho_pasta,
            angulo=angulo_graus,
            new_line=new_line
        )
        # CASO O ANAREDE TENHA DADO ERRO DEVIDO A NÃO CONVERGÊNCIA, ENCERRA o PROCESSO DO ANAREDE
        # DE FORMA FORÇADA PARA EVITAR QUE O ANAREDE FIQUE ABERTO E IMPEDINDO A PRÓXIMA EXECUÇÃO
        # Caminho completo do executável
        caminho_exe = r"C:\CEPEL\Anarede\V130001\\ANAREDE.exe"
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                # Verifica se o processo do ANAREDE ainda está em execução e se sim finaliza.
                if proc.info['name'] == "ANAREDE.exe":
                    if 'exe' in proc.info and proc.info['exe'] and os.path.samefile(proc.info['exe'], caminho_exe):
                        proc.kill()
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, FileNotFoundError):
                continue
    return plot_list, exit_list

# def executar_anarede_sincrono(arquivo_mestre: Path,
#                               anarede_executable: Path,
#                               timeout: int = 300) -> bool:
#     """
#     Executa o ANAREDE de forma SÍNCRONA (aguarda conclusão)
#     """
#     try:
#         comando = f'"{anarede_executable}" "{arquivo_mestre}"'
#         subprocess.run(
#             comando,
#             shell=True,
#             capture_output=True,
#             text=True,
#             timeout=timeout,
#         )
#         return True
            
#     except subprocess.TimeoutExpired:
#         print(f"Timeout: ANAREDE excedeu {timeout} segundos")
#         # Força finalização
#         subprocess.run('taskkill /f /im ANAREDE.exe', shell=True, capture_output=True)
#         return False
#     except Exception as e:
#         print(f"Erro ao executar ANAREDE: {e}")
#         return False