import math
import pandas as pd

from utils_seguida import *

from graph import *

import sys

if __name__ == "__main__":
    # Solicita arquivo de entrada (.pwf) ao usuário
    caminho_caso_base = selecionar_arquivo_base()
    if caminho_caso_base is None:
        print("Execução cancelada pelo usuário.")
        sys.exit(0)

    # Lê o arquivo de entrada (.pwf) e armazena as linhas em uma lista
    linhas = []
    with open(caminho_caso_base) as f: 
            linhas = f.readlines()

    # Solicita barra a ser analisada
    while True:
        try:
            target_bar = int(input("Número da barra para análise: "))
            if check_exist_bar(linhas, target_bar):
                target_bar = str(target_bar)
                break
            else:
                print("Barra inexistente no caso selecionado anteriormente ou não é uma barra de carga.")
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    # Solicita número de aberturas (angulos)
    while True:
        try:
            aberturas = int(input("Número de aberturas (ângulos): "))
            break
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    # Solicita valor do passo a usar para aumento da carga, em porcentagem
    while True:
        try:
            passo = int(input("Valor do passo (%): "))
            break
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    # Solicita valor de redução passo, em X vezes
    while True:
        try:
            reduce = int(input("Valor para redução do passo (em X vezes): "))
            break
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    if linhas:
        target_line, Pl_original, Ql_original = get_line_pq(linhas, target_bar)

    Sl = math.sqrt(Pl_original**2 + Ql_original**2)

    # Calcula o fator de aumento com base no passo e na potência aparente original
    factor = (passo / 100) * Sl

    # Cria a lista de ângulos que serão usados na análise variando de 45° a 45°+(360/abeturas)
    angulos = [
        math.pi/4 + i*(2*math.pi/aberturas)
        for i in range(aberturas)
    ]

    # Cria pasta base do projeto
    pasta_base = r"C:\PyTSOFlex"

    # Cria a lista com os caminhos das pastas
    pastas = [
        os.path.join(
            pasta_base,
            str(int(round(math.degrees(angulo))))
        )
        for angulo in angulos
    ]

    # Reescreve arquivo com as saídas para os relatórios com nomes corretos e no diretório corretp
    if linhas:
        linhas = create_report(linhas, pasta_base)
        #Reescreve arquivo com as saídas para os relatórios no diretório do ângulo
        nome, extensao = os.path.splitext(os.path.basename(caminho_caso_base))
        caminho_caso_base = os.path.join(pasta_base, f"{nome}{extensao}")
        with open(caminho_caso_base, "w") as f:
            f.writelines(linhas)

        # Variável a ser passada para a função processa_angulo, contendo a string da linha da barra alvo.
        string_barra_alvo = linhas[target_line]

    # Cria arquivo para leitura do caso base e criação do Save Case de cada ângulo
    caminho_executa_base = create_base_case(caminho_caso_base, pasta_base, angulos)

    # Processa arquivo base criado
    check_processo_base = executa_anarede_sincrono(caminho_executa_base, pastas)
    print(f"Processamento do caso base {'concluído' if check_processo_base else 'não concluído'}.")

    violou_tensao_base = False
    violou_fluxo_base = False
    violou_geracao_base = False
    minimal_step = False


    exit_list_final = []
    plot_list_final = []

    # Analisa execução do caso base:
    # 1- Se o caso base convergiu e não teve violação, a execução começa de fato
    # 2- Se o caso base convergiu, mas teve violação, o passo é diminuído e a execução inicia
    # 3- Se o caso base não convergiu, a execução é interrompida
    # Lê o relatório para verificar convergência
    convergencia_base = check_convergence(pasta_base)
    if convergencia_base:
        iteracao = 1

        linhas_monitoradas = read_monitoring(pasta_base)
        # Verifico se nessa condição houve violação de tensão
        violou_tensao_base = check_tensao(linhas_monitoradas)
        # Verifico se nessa condição houve violação de fluxo
        violou_fluxo_base = check_fluxo(linhas_monitoradas)
        # Verifico se nessa condição houve violação de geração
        violou_geracao_base = check_geracao(pasta_base)

        # Se violou qualquer um dos três itens, o passo é diminuído e a execução continua
        if violou_tensao_base or violou_fluxo_base or violou_geracao_base:
            factor = factor / reduce
            minimal_step = True


        exit_list_final.append({
            "Ângulo": "-",
            "Iteracao": iteracao,
            "Característica": "Original",
            "PL": f"{Pl_original:5.2f}"[:5],
            "QL": f"{Ql_original:5.2f}"[:5],
            "Violação de Tensão": "Sim" if violou_tensao_base else "Não",
            "Violação de Fluxo": "Sim" if violou_fluxo_base else "Não",
            "Violação de Geração": "Sim" if violou_geracao_base else "Não",
            "Convergiu": True,
        })
        plot_list_final.append({
            "Ângulo": "-",
            "Característica": "Original",
            "PL": f"{Pl_original:5.2f}"[:5],
            "QL": f"{Ql_original:5.2f}"[:5],
            "Violação de Tensão": "Sim" if violou_tensao_base else "Não",
            "Violação de Fluxo": "Sim" if violou_fluxo_base else "Não",
            "Violação de Geração": "Sim" if violou_geracao_base else "Não",
            "Convergiu": "Sim" if convergencia_base else "Não",
        })

        # Caso base convergido, as execuções dos ângulos são iniciadas
        status_angulos = {
            angulo: {
                "convergiu": True,
                "violou_tensao": violou_tensao_base,
                "violou_fluxo": violou_fluxo_base,
                "violou_geracao": violou_geracao_base,
                "first_divergence": False,
                "first_tensao": False,
                "first_fluxo": False,
                "first_geracao": False,
                "minimal_step": minimal_step,
                "iteracao": iteracao,
                "Pl": Pl_original,
                "Ql": Ql_original
            }
            for angulo in angulos
        }

        angulos_ativos = list(angulos)

        pastas_ativas = pastas
        angulos_nao_executaram = []
        arquivos_execucao = []
        proximos_ativos = []

        # Cria os arquivos para execução da primeira iteração de cada ângulo, formando o arquivo mestre.
        # Nesse momento a execução é realizada, mas os status de cada ângulo ainda não são atualizados, 
        # pois a análise é feita na função processa_angulo, que é chamada na próxima etapa. 
        # Os status nesse ponto são ainda da execução do caso base.
        for angulo in angulos_ativos:
            caminho_caso, Pl, Ql = cria_primeira_iteracao(
                pasta_base,
                angulo,
                Pl_original,
                Ql_original,
                factor,
                string_barra_alvo
            )
            status_angulos[angulo]["Pl"] = Pl
            status_angulos[angulo]["Ql"] = Ql
            arquivos_execucao.append(caminho_caso)

        # Gera arquivo de execução para os ângulos que continuam
        linhas = []
        for caminho_caso in arquivos_execucao:
            linhas.extend([
                "ULOG\n",
                "1\n",
                f"{caminho_caso}\n",
            ])
        linhas.extend([
            "DOSC\n",
            "TASKKILL /T /F /IM ANAREDE.EXE\n",
            "99999\n",
            "FIM"
        ])
        caminho_executa_mestre = os.path.join(pasta_base, f"caso_mestre.pwf")
        with open(caminho_executa_mestre, "w", encoding="utf-8") as f:
            f.writelines(linhas)
        respostas = executa_anarede_sincrono(caminho_executa_mestre, pastas_ativas)
        # Busco os angulos que não executaram na rodada
        angulos_nao_executaram = [
            angulo
            for angulo, resposta in respostas.items()
            if resposta == 'Não executado'
        ]
        # Se tenho angulos que não executaram, removo da lista de ativos para a próxima rodada
        if len(angulos_nao_executaram) > 0:
            angulos_ativos = [
                angulo
                for angulo in proximos_ativos
                if int(round(math.degrees(angulo))) not in angulos_nao_executaram
            ]
    
        pastas_ativas = [
            os.path.join(
                pasta_base,
                str(int(round(math.degrees(angulo))))
            )
            for angulo in angulos_ativos
        ]


        while angulos_ativos:
            proximos_ativos = []
            arquivos_execucao = []

            for angulo in angulos_ativos:
                status_angulo = status_angulos[angulo]
                plot_local, exit_local, caminho_caso, status_atualizado = processa_angulo(
                    pasta_base,
                    pastas_ativas,
                    angulo,
                    status_angulo,
                    factor,
                    reduce,
                    string_barra_alvo
                )

                status_angulos[angulo] = status_atualizado

                plot_list_final.extend(plot_local)
                exit_list_final.extend(exit_local)

                if status_atualizado["convergiu"]:
                    proximos_ativos.append(angulo)
                    arquivos_execucao.append(caminho_caso)

            # Remove RELAT.OUT já analisado.
            for pasta in pastas_ativas:
                relatorio = os.path.join(pasta, "RELAT.OUT")
        
                if os.path.exists(relatorio):
                    os.remove(relatorio)

            # Se na rodada tive angulos que não executaram, adiciono eles na lista de próximos ativos para 
            # a próxima rodada e nos arquivos para execução.
            if len(angulos_nao_executaram) > 0:
                angulos_nao_executaram.sort()
                for angulo_graus in angulos_nao_executaram:
                    angulo_original = next(
                        angulo
                        for angulo in angulos
                        if int(round(math.degrees(angulo))) == angulo_graus
                    )
                    if angulo_original not in proximos_ativos:
                        proximos_ativos.append(angulo_original)
                proximos_ativos.sort()
                # Adiciono os arquivos de execução dos ângulos que não executaram na rodada
                for angulo in angulos_nao_executaram:
                    pasta = os.path.join(pasta_base, str(angulo))
                    caminho_pasta = os.path.abspath(pasta)
                    caminho_caso = os.path.join(caminho_pasta, f"caso_{angulo}.pwf")
                    arquivos_execucao.append(caminho_caso)

                pastas_ativas = [
                    os.path.join(
                        pasta_base,
                        str(int(round(math.degrees(angulo))))
                    )
                    for angulo in proximos_ativos
                ]

            if not proximos_ativos:
                break

            # Gera arquivo de execução para os ângulos que continuam
            linhas = []
            for caminho_caso in arquivos_execucao:
                linhas.extend([
                    "ULOG\n",
                    "1\n",
                    f"{caminho_caso}\n",
                ])
            linhas.extend([
                "DOSC\n",
                "TASKKILL /T /F /IM ANAREDE.EXE\n",
                "99999\n",
                "FIM"
            ])
            caminho_executa_mestre = os.path.join(pasta_base, f"caso_mestre.pwf")
            with open(caminho_executa_mestre, "w", encoding="utf-8") as f:
                f.writelines(linhas)
            respostas = executa_anarede_sincrono(caminho_executa_mestre, pastas_ativas)
            # Busco os angulos que não executaram na rodada
            angulos_nao_executaram = [
                angulo
                for angulo, resposta in respostas.items()
                if resposta == 'Não executado'
            ]
            # Se tenho angulos que não executaram, removo da lista de ativos para a próxima rodada
            if len(angulos_nao_executaram) > 0:
                angulos_ativos = [
                    angulo
                    for angulo in proximos_ativos
                    if int(round(math.degrees(angulo))) not in angulos_nao_executaram
                ]
            else:
                angulos_ativos = proximos_ativos

            pastas_ativas = [
                os.path.join(
                    pasta_base,
                    str(int(round(math.degrees(angulo))))
                )
                for angulo in angulos_ativos
            ]
    else:
        print("❌ O caso base não convergiu. Revise o caso selecionado. A execução será interrompida.")
        sys.exit(0)


    exit_df = pd.DataFrame(exit_list_final)
    nome_arquivo = os.path.splitext(os.path.basename(caminho_caso_base))[0]
    arq_resultado = f"resultado_{nome_arquivo}.xlsx"
    exit_df.to_excel(arq_resultado, index=False)

    plot_df = pd.DataFrame(plot_list_final)
    arq_plot = f"plot_{nome_arquivo}.xlsx"
    plot_df.to_excel(arq_plot, index=False) 

    plot = PlotFlexibilidade(plot_df)

    plot.gerar_relatorio()