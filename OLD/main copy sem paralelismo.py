import math

from utils_copy import *
import pandas as pd

from graph import *

from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

if __name__ == "__main__":

    # Solicita barra a ser analisada
    while True:
        try:
            target_bar = int(input("Número da barra para análise: "))
            target_bar = str(target_bar)
            break
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    # Solicita número de aberturas (angulos)
    while True:
        try:
            aberturas = int(input("Número de aberturas (ângulos): "))
            break
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    converged = True
    violou_tensao = False
    violou_fluxo = False
    violou_geracao = False

    first_divergence = False
    first_tensao = False
    first_fluxo = False
    first_geracao = False

    minimal_step = False

    observacao = ''

    Pl_old, Ql_old = 0, 0

    #Leitura do PWF Original para verificação da linha de modificação
    # Caminho do arquivo de entrada (.pwf)
    arquivo_pwf = r"C:\Users\Usuario\Documents\Projeto_Regiao_Flexibilidade\PyTSOFlex\Tutorial_2_barras.pwf"

    # separa nome e extensão
    base, ext = os.path.splitext(arquivo_pwf)


    with open(arquivo_pwf) as f: 
        lines = f.readlines()
        target_line, Pl_original, Ql_original = check_line_pq(lines, target_bar)

    Sl = math.sqrt(Pl_original**2 + Ql_original**2)

    # Solicita ao usuário valor do passo a usar para aumento da carga, em porcentagem
    while True:
        try:
            passo = int(input("Valor do passo (%): "))
            break
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    # Solicita ao usuário valor de redução passo
    while True:
        try:
            reduce = int(input("Valor para redução do passo (em X vezes): "))
            break
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

    # Calcula o fator de aumento com base no passo e na potência aparente original
    factor = (passo / 100) * Sl

    # Cria a lista de ângulos que serão usados na análise variando de 45° a 45°+(360/abeturas)
    angulos = [
        math.pi/4 + i*(2*math.pi/aberturas)
        for i in range(aberturas)
    ]
    
    exit_list_final = []
    plot_list_final = []
    for angulo in angulos:
        plot_local, exit_local = processa_angulo(
            angulo,
            Pl_original,
            Ql_original,
            arquivo_pwf,
            factor,
            reduce,
            lines,
            target_line
        )
        plot_list_final.extend(plot_local)
        exit_list_final.extend(exit_local)

    exit_df = pd.DataFrame(exit_list_final)
    nome_arquivo = os.path.splitext(os.path.basename(arquivo_pwf))[0]
    arq_resultado = f"resultado_{nome_arquivo}.xlsx"
    exit_df.to_excel(arq_resultado, index=False)

    plot_df = pd.DataFrame(plot_list_final)
    arq_plot = f"plot_{nome_arquivo}.xlsx"
    plot_df.to_excel(arq_plot, index=False)

    plot = PlotFlexibilidade(plot_df)

    plot.gerar_relatorio()