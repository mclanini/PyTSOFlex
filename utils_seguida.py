import shutil
import subprocess
import time
import psutil
import os
import time
import math
import tkinter as tk
from tkinter import filedialog

def selecionar_arquivo_base():
    while True:
        try:
            print("Selecionar arquivo base:")
            print("1 - Sim")
            print("2 - Cancelar")

            opcao = int(input("Opção: "))

            if opcao == 1:
                root = tk.Tk()
                root.withdraw()
                caminho_caso_base = filedialog.askopenfilename(
                    title="Selecionar arquivo base",
                    filetypes=[
                        ("Arquivos PWF", "*.pwf"),
                        ("Todos os arquivos", "*.*")
                    ]
                )
                root.destroy()
                if caminho_caso_base:
                    caminho_caso_base = os.path.normpath(caminho_caso_base)
                    return caminho_caso_base
                print("Nenhum arquivo selecionado.")
            elif opcao == 2:
                return None
            else:
                print("Opção inválida. Digite 1 ou 2.")
        except ValueError:
            print("Valor inválido. Digite 1 ou 2.")

def check_exist_bar(lines, target_bar):
    #0         1         2         3         4         5         6         7          
    #01234567890123456789012345678901234567890123456789012345678901234567890123456789
    #(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
    dentro_dbar = False
    for linha in lines:
        if not dentro_dbar:
            if linha.strip() == "DBAR":
                dentro_dbar = True
            continue
        if linha.strip() == "99999":
            return False
        if linha[:5].strip() == str(target_bar):
            if linha[7] == str(0):
                return True
    return False

def get_line_pq(lines, target_bar):
    #0         1         2         3         4         5         6         7          
    #01234567890123456789012345678901234567890123456789012345678901234567890123456789
    #(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
    idx_dbar = 9e100
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

def create_base_case(caminho_caso_base, pasta_base, angulos):
    caminho_executa_base = os.path.join(pasta_base, f"caso_base.pwf")
    linhas = [
        "ULOG\n",
        "1\n",
        f"{caminho_caso_base}\n",
    ]
    for angulo in angulos:
        # Cria as pastas de cada ângulo dentro da pasta base nessa primeira função
        angulo_graus = int(round(math.degrees(angulo)))
        pasta = os.path.join(pasta_base, str(angulo_graus))
        # Se já existir, remove tudo
        if os.path.exists(pasta):
            shutil.rmtree(pasta)
        # Cria novamente a pasta vazia
        os.makedirs(pasta)
        # Caminho completo
        caminho_pasta = os.path.abspath(pasta)
        linhas.extend([
            "ULOG\n",
            "2\n",
            f"{caminho_pasta}\TESTE_{angulo_graus}.SAV\n",
            "ARQV INIC NOVO\n",
            "SIM\n",
            "TITU\n",
            "Original\n",
            "ARQV GRAV\n",
            "01\n",
        ])
    linhas.extend([
        "DOSC\n",
        "TASKKILL /T /F /IM ANAREDE.EXE\n",
        "99999\n",
        "FIM"
    ])
    with open(caminho_executa_base, "w", encoding="utf-8") as f:
        f.writelines(linhas)
        return caminho_executa_base

def executa_anarede_sincrono(arquivo_mestre, pastas, intervalo_verificacao=1):
    """
    Executa o ANAREDE e monitora a convergência dos casos.

    Os casos são executados em ordem crescente dos ângulos.

    Ao encontrar a primeira divergência:
    - o ângulo divergente recebe False;
    - todos os ângulos seguintes recebem 'Não executado';
    - o ANAREDE é abortado.

    Retorna:
        {angulo: True/False/'Não executado'}
    """

    caminho_exe = r"C:\CEPEL\Anarede\V130001\ANAREDE.exe"
    comando = f'"{caminho_exe}" "{arquivo_mestre}"'
    # Dicionário inicial
    respostas = {
        int(os.path.basename(pasta)): None
        for pasta in pastas
    }
    try:
        processo = subprocess.Popen(
            comando,
            shell=True
        )
        while processo.poll() is None:
            for i, pasta in enumerate(pastas):
                angulo = int(os.path.basename(pasta))
                convergiu = check_convergence_execucao_anarede(pasta)
                # Arquivo ainda não existe ou está vazio
                if convergiu is None:
                    continue
                # Caso convergiu
                if convergiu is True:
                    respostas[angulo] = True
                    # Se todos já convergiram, encerra
                    if all(resposta is True for resposta in respostas.values()):
                        print("Todos os ângulos convergiram.")
                    continue
                # Caso divergiu
                if convergiu is False:
                    respostas[angulo] = False
                    # Todos os ângulos seguintes recebem 'Não executado'
                    for pasta_restante in pastas[i + 1:]:
                        angulo_restante = int(
                            os.path.basename(pasta_restante)
                        )
                        respostas[angulo_restante] = 'Não executado'
                    print(f"Não convergiu no ângulo {angulo}°")
                    print("Abortando execução do ANAREDE...")
                    subprocess.run(
                        "TASKKILL /T /F /IM ANAREDE.EXE",
                        shell=True,
                        capture_output=True
                    )
                    return respostas
            time.sleep(intervalo_verificacao)
        return respostas
    except Exception as e:
        print(f"Erro ao executar ANAREDE: {e}")
        return respostas

def cria_caso_angulo(iteracao, caminho_pasta, angulo, new_line):
    caminho_caso = os.path.join(caminho_pasta, f"caso_{angulo}.pwf")
    linhas = [
        "DOSC\n",
        f"DEL {caminho_pasta}\*.out\n",
        "99999\n",
        "ULOG\n",
        "2\n",
        f"{caminho_pasta}\TESTE_{angulo}.SAV\n",
        "ARQV REST\n",
        f"{iteracao:02d}\n",
        "DOPC\n",
        "FILE L\n",
        "99999\n",
        "DBAR IMPR\n",
        f"(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10\n",
        f"{new_line}\n",
        "99999\n",
        "ULOG\n",
        "4\n",
        f"{caminho_pasta}\RELAT.OUT\n",
        "EXLF NEWT QLIM FILE\n",
        "RELA RBAR RLIN FILE\n",
        "TITU\n",
        f"Direcao_{angulo}_caso_{iteracao}\n",
        "ARQV GRAV\n",
        f"{iteracao+1:02d}\n",
        "ULOG\n",
        "4\n",
        f"{caminho_pasta}\REMON.OUT\n",
        "RELA RMON MOCT MOCF MOCG FILE\n",
        "ULOG\n",
        "4\n",
        f"{caminho_pasta}\REMON_GER.OUT\n",
        "RELA RGEL\n",
        "FIM"
    ]
    with open(caminho_caso, "w", encoding="utf-8") as f:
        f.writelines(linhas)
    return caminho_caso

def create_report(lines, caminho_pasta):
    encontrou = False
    # Faz um único strip para evitar múltiplos
    lines_strip = [line.strip() for line in lines]
    for i in range(len(lines_strip) - 1):
        if lines_strip[i] == "ULOG" and lines_strip[i + 1] == "4":
            encontrou = True
            # Se eu já tenho uma saída com ULOG 4 eu reescrevo para garantir o relatório correto
            bloco = [
                f"{caminho_pasta}\RELAT.OUT\n",
                "EXLF NEWT QLIM FILE\n",
                "RELA RBAR RLIN FILE\n",
                "ULOG\n",
                "4\n",
                f"{caminho_pasta}\REMON.OUT\n",
                "RELA RMON MOCT MOCF MOCG FILE\n",
                "ULOG\n",
                "4\n",
                f"{caminho_pasta}\REMON_GER.OUT\n",
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
            f"{caminho_pasta}\RELAT.OUT\n",
            "EXLF NEWT QLIM FILE\n",
            "RELA RBAR RLIN FILE\n",
            "ULOG\n",
            "4\n",
            f"{caminho_pasta}\REMON.OUT\n",
            "RELA RMON MOCT MOCF MOCG FILE\n",
            "ULOG\n",
            "4\n",
            f"{caminho_pasta}\REMON_GER.OUT\n",
            "RELA RGEL\n",
        ]
        for i, linha in enumerate(lines_strip):
            if linha == "FIM":
                lines[i:i] = bloco
                break
    return lines

def check_convergence_execucao_anarede(pasta):
    relatorio = os.path.join(pasta, "RELAT.OUT")
    # Arquivo ainda não existe
    if not os.path.exists(relatorio):
        return None
    # Arquivo existe, mas está vazio
    if os.path.getsize(relatorio) == 0:
        return None
    try:
        with open(relatorio, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip() == "CONVERGENCIA FINAL":
                    return True
                if "DIVERGENTE" in line.strip().upper() or "NAO CONVERGENTE" in line.strip().upper():
                    return False
    except (PermissionError, OSError):
        return None
    # Arquivo existe, tem conteúdo,
    # mas não possui "CONVERGENCIA FINAL", mas ainda pode possuir.
    return None

def check_convergence(pasta):
    # Caminho do arquivo de entrada (.pwf)
    relatorio = os.path.join(pasta, "RELAT.OUT")
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
    relatorio = os.path.join(pasta, "REMON.OUT")
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
    # # Caminho do arquivo de entrada (.pwf)
    # relatorio = os.path.join(pasta, "REMON_GER.OUT")
    # if os.path.getsize(relatorio) == 0:
    #     violou_geracao = False
    # else:
    #     violou_geracao = True
    # ----- IMPORTANTE -----
    # A verificação de violação de geração foi desativada temporariamente, pois o método não está 
    # funcionando corretamente. Será preciso pesquisar qual a verdadeira saída do ANAREDE 
    # para indicar violação de geração.
    # ----- IMPORTANTE -----
    violou_geracao = False
    return violou_geracao

def reduce_step(Pl, Ql, factor_P, factor_Q, reduce_step):
    # Retorno pro último valor de Pl e Ql antes da divergência e diminuo o passo
    Pl -= factor_P
    Ql -= factor_Q
    factor_P /= reduce_step
    factor_Q /= reduce_step
    minimal_step = True
    return Pl, Ql, factor_P, factor_Q, minimal_step

def cria_primeira_iteracao(pasta_base, angulo, Pl_original, Ql_original, factor, string_barra_alvo):
    Pl = Pl_original
    Ql = Ql_original
    caminho_caso = None

    angulo_graus = int(round(math.degrees(angulo)))
    # Pasta do ângulo
    pasta = os.path.join(pasta_base, str(angulo_graus))
    caminho_pasta = os.path.abspath(pasta)

    # Calcula o fator de aumento para a potência ativa daquele angulo
    factor_P = factor * math.cos(angulo)
    # Calcula o fator de aumento para a potência reativa daquele angulo
    factor_Q = factor * math.sin(angulo)

    # Atualiza os valores de Pl e Ql com base no fator calculado (novo valor após caso base convergido)
    Pl += factor_P
    Ql += factor_Q
    #cria linha atualizada com novos valores de Pl e Ql para o caso_angulo.pwf
    #0         1         2         3         4         5         6         7          
    #01234567890123456789012345678901234567890123456789012345678901234567890123456789
    #(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
    new_line = (
        string_barra_alvo[:5] +
        "M" +
        " " * 52 +
        f"{Pl:5.2f}"[:5] +
        f"{Ql:5.2f}"[:5]
    )
    caminho_caso = cria_caso_angulo(
        iteracao=1,
        caminho_pasta=caminho_pasta,
        angulo=angulo_graus,
        new_line=new_line
    )
    return caminho_caso, Pl, Ql

def processa_angulo(pasta_base, pastas, angulo, status_angulo, factor, reduce, string_barra_alvo):
#   Inicialização das variáveis de controle
    converged = True
    violou_tensao = status_angulo["violou_tensao"]
    violou_fluxo = status_angulo["violou_fluxo"]
    violou_geracao = status_angulo["violou_geracao"]
#   Inicialização das variáveis de controle
    first_divergence = status_angulo["first_divergence"]
    first_tensao = status_angulo["first_tensao"]
    first_fluxo = status_angulo["first_fluxo"]
    first_geracao = status_angulo["first_geracao"]
#   Inicialização das variáveis de controle
    minimal_step = status_angulo["minimal_step"]
#   Inicialização das variáveis de controle
    observacao = ''
    plot_list = []
    exit_list = []
    iteracao = status_angulo["iteracao"]
    Pl = status_angulo["Pl"]
    Ql = status_angulo["Ql"]
    Pl_old, Ql_old = 0, 0
    caminho_caso = None

#   INICIA O PROCESSO DE ANÁLISE PARA O ÂNGULO ESPECÍFICO
    angulo_graus = int(round(math.degrees(angulo)))
    # Pasta do ângulo
    pasta = os.path.join(pasta_base, str(angulo_graus))
    caminho_pasta = os.path.abspath(pasta)

    # Calcula o fator de aumento para a potência ativa daquele angulo
    factor_P = factor * math.cos(angulo)
    # Calcula o fator de aumento para a potência reativa daquele angulo
    factor_Q = factor * math.sin(angulo)

    # Como factor são recalculados sempre, preciso voltar o valor para reduzido se o passo na iteração
    # anterior estava reduzido.
    if minimal_step:
        factor_P /= reduce
        factor_Q /= reduce

    # A execução é verificada levando em consideração se existe ou não o arquivo RELAT.OUT na pasta do 
    # ângulo. Se não existir, significa que o ANAREDE não foi executado ou não gerou o relatório.
    executed = (
        os.path.exists(os.path.join(caminho_pasta, "RELAT.OUT"))
    )
    if not executed:
        print(f"❌ Falha ao executar o ANAREDE ou gerar um dos relatórios. ANGULO: {angulo_graus}° | CASO: {iteracao}")
        return [], [], None, None
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
                        first_tensao = False
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
                            Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, reduce)
                        # Se violou tensão e já tive alguma violação (qualquer uma) não reduzo o passo
                        # pois já está reduzido e então já tenho o ponto exato de violação de tensão
                        else:
                            violou_tensao = True
                            print(f"✅ Primeira violação de tensão atingida, pois passo já está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                            plot_list.append({
                                "Ângulo": f"{math.degrees(angulo):.0f}°",
                                "Característica": "Modificado",
                                "PL": f"{Pl:5.2f}"[:5],
                                "QL": f"{Ql:5.2f}"[:5],
                                "Violação de Tensão": "Sim"
                            })
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
                            Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, reduce)
                        # Se violou fluxo e já tive alguma violação (qualquer uma) não reduzo o passo
                        # pois já está reduzido e então já tenho o ponto exato de violação de fluxo
                        else:
                            violou_fluxo = True
                            print(f"✅ Ponto de violação de fluxo encontrado, pois passo já está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                            plot_list.append({
                                "Ângulo": f"{math.degrees(angulo):.0f}°",
                                "Característica": "Modificado",
                                "PL": f"{Pl:5.2f}"[:5],
                                "QL": f"{Ql:5.2f}"[:5],
                                "Violação de Fluxo": "Sim"
                            })
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
                            Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, reduce)
                        # Se violou geração e já tive alguma violação (qualquer uma) não reduzo o passo
                        else:
                            violou_geracao = True
                            print(f"✅ Ponto de violação de geração encontrado, pois passo já está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
                            plot_list.append({
                                "Ângulo": f"{math.degrees(angulo):.0f}°",
                                "Característica": "Modificado",
                                "PL": f"{Pl:5.2f}"[:5],
                                "QL": f"{Ql:5.2f}"[:5],
                                "Violação de Geração": "Sim"
                            })
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
                status_atualizado = {
                    "convergiu": False,
                    "violou_tensao": violou_tensao,
                    "violou_fluxo": violou_fluxo,
                    "violou_geracao": violou_geracao,
                    "first_divergence": first_divergence,
                    "first_tensao": first_tensao,
                    "first_fluxo": first_fluxo,
                    "first_geracao": first_geracao,
                    "minimal_step": minimal_step,
                    "iteracao": iteracao,
                    "Pl": Pl,
                    "Ql": Ql
                }
                return plot_list, exit_list, caminho_caso, status_atualizado
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
                Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, reduce)
            # Se divergiu e já tive alguma divergência, não reduzo o passo e tenho o ponto exato
            # da divergência, então o processo é encerrado.
            else:
                print(f"✅ Ponto de divergência encontrado, pois o passo está minimizado. ANGULO: {angulo_graus}° | CASO: {iteracao}")
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
                status_atualizado = {
                    "convergiu": False,
                    "violou_tensao": violou_tensao,
                    "violou_fluxo": violou_fluxo,
                    "violou_geracao": violou_geracao,
                    "first_divergence": first_divergence,
                    "first_tensao": first_tensao,
                    "first_fluxo": first_fluxo,
                    "first_geracao": first_geracao,
                    "minimal_step": minimal_step,
                    "iteracao": iteracao,
                    "Pl": Pl,
                    "Ql": Ql
                }
                return plot_list, exit_list, caminho_caso, status_atualizado
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
        string_barra_alvo[:5] +
        "M" +
        " " * 52 +
        f"{Pl:5.2f}"[:5] +
        f"{Ql:5.2f}"[:5]
    )
    caminho_caso = cria_caso_angulo(
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

    status_atualizado = {
        "convergiu": True,
        "violou_tensao": violou_tensao,
        "violou_fluxo": violou_fluxo,
        "violou_geracao": violou_geracao,
        "first_divergence": first_divergence,
        "first_tensao": first_tensao,
        "first_fluxo": first_fluxo,
        "first_geracao": first_geracao,
        "minimal_step": minimal_step,
        "iteracao": iteracao,
        "Pl": Pl,
        "Ql": Ql
    }
    
    return plot_list, exit_list, caminho_caso, status_atualizado