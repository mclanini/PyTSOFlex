import math

from utils import *
import pandas as pd

from graph import *


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

#Leitura do PWF Original para verificação da linha de modificação
# Caminho do arquivo de entrada (.pwf)
arquivo_pwf = r"C:\Users\Usuario\Documents\Projeto Regiao Flexibilidade\PyTSOFlex\Tutorial 2 barras.pwf"

# separa nome e extensão
base, ext = os.path.splitext(arquivo_pwf)

# cria novo nome
arquivo_pwf_modificado = f"{base}_modificado{ext}"

with open(arquivo_pwf) as f: 
    lines = f.readlines()
    target_line, Pl_original, Ql_original = check_line_pq(lines, target_bar)

# Potência Ativa Original
Pl = Pl_original
# Potência Reativa Original
Ql = Ql_original
# Potência Aparente Original
Sl = math.sqrt(Pl**2 + Ql**2)

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

# Modifica linha para salvar relatório com nome diferente caso exista o ULOG e não sobrepor o original
lines = create_report(lines)

exit_list = []
iteracao = 0
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

plot_list = []
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

for angulo in angulos:
    # Calcula o fator de aumento para a potência ativa daquele angulo
    factor_P = factor/math.cos(angulo)
    # Calcula o fator de aumento para a potência reativa daquele angulo
    factor_Q = factor/math.sin(angulo)
    while converged == True:
        #Atualiza valores (em memória) de Pl e Ql
        # Comportamento:
        # | Quadrante | cos | sin |   ΔPl   |   ΔQl   |
        # | --------- | --- | --- | ------- | ------- |
        # |  0°–90°   |  +  |  +  | +factor | +factor |
        # | 90°–180°  |  -  |  +  | -factor | +factor |
        # | 180°–270° |  -  |  -  | -factor | -factor |
        # | 270°–360° |  +  |  -  | +factor | -factor |

        # Pl += factor_P * (1 if math.cos(angulo) >= 0 else -1)
        # Ql += factor_Q * (1 if math.sin(angulo) >= 0 else -1)
        Pl += factor_P
        Ql += factor_Q

        #Atualiza linha
        #0         1         2         3         4         5         6         7          
        #01234567890123456789012345678901234567890123456789012345678901234567890123456789
        #(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
        new_line = (
            lines[target_line][:58] +
            f"{Pl:5.2f}"[:5] +
            f"{Ql:5.2f}"[:5] +
            lines[target_line][68:]
        )
        lines[target_line] = new_line

        #Reescreve arquivo com a linha modificada
        with open(arquivo_pwf_modificado, "w") as f:
            f.writelines(lines)
        
        # Chamar o ANAREDE encapsulado para rodar o arquivo modificado
        executed = execute_anarede(arquivo_pwf_modificado)
        # Espera alguns segundos
        time.sleep(1)
        # Verifica criação do arquivo de relatório para garantir que o ANAREDE rodou
        executed_2 = os.path.exists("RELAT_NEW.OUT") and os.path.exists("REMON.OUT") and os.path.exists("REMON_GER_NEW.OUT")
        print(executed, executed_2)
        if not executed or not executed_2:
            print("❌ Falha ao executar o ANAREDE ou gerar um dos relatórios.")
            break
        else:
            print("✅ ANAREDE executado e relatório gerado com sucesso.")
            # Lê o relatório para verificar convergência
            converged = check_convergence()
            if converged:
                print("🔄 Convergência atingida, violações serão analisadas...")
                lines_monitoring = read_monitoring()
                # ---------------- ANÁLISE DE TENSÃO ----------------
                # Se ainda não violou tensão entro no IF e continuo verificando a cada iteração
                if not violou_tensao:
                    # Verifico se nessa condição houve violação de tensão
                    violou_tensao = check_tensao(lines_monitoring)
                    if violou_tensao:
                        print("✅ Tensão violou.")
                        # Se eu violei tensão e já tive a primeira violação DE TENSÃO, 
                        # então a análise de tensão acaba
                        if first_tensao:
                            print("✅ Ponto de violação de tensão encontrado.")
                            violou_tensao = True
                            # Se eu não estiver verificando nenhuma outra violação,
                            # posso retornar o passo para o normal
                            if not (first_fluxo and first_geracao) and minimal_step:
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
                                print("✅ Primeira violação de tensão atingida, passo será reduzido.")
                                violou_tensao = False
                                # Retorno pro último valor de Pl e Ql antes da divergência 
                                # e diminuo o passo
                                Pl_old, Ql_old = Pl, Ql
                                Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                            # Se violou tensão e já tive alguma violação (qualquer uma) não reduzo o passo
                            else:
                                first_tensao = True
                                print("✅ Primeira violação de tensão atingida. Passo já está minimizado.")
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
                        print("✅ Fluxo violou.")
                        print(lines_monitoring)
                        # Se eu violei fluxo e já tive a primeira violação DE FLUXO, 
                        # então a análise de fluxo acaba
                        if first_fluxo:
                            print("✅ Ponto de violação de fluxo encontrado.")
                            violou_fluxo = True
                            # Se eu não estiver verificando nenhuma outra violação,
                            # posso retornar o passo para o normal
                            if not (first_tensao and first_geracao) and minimal_step:
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
                                print("✅ Primeira violação de fluxo atingida, passo será reduzido.")
                                violou_fluxo = False
                                # Retorno pro último valor de Pl e Ql antes da divergência 
                                # e diminuo o passo
                                Pl_old, Ql_old = Pl, Ql
                                Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                            # Se violou fluxo e já tive alguma violação (qualquer uma) não reduzo o passo
                            else:
                                first_fluxo = True
                                print("✅ Primeira violação de fluxo atingida. Passo já está minimizado.")
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
                    violou_geracao = check_geracao()
                    if violou_geracao:
                        print("✅ Geração violou.")
                        # Se eu violei geração e já tive a primeira violação DE GERAÇÃO, 
                        # então a análise de geração acaba
                        if first_geracao:
                            print("✅ Ponto de violação de geração encontrado.")
                            violou_geracao = True
                            # Se eu não estiver verificando nenhuma outra violação,
                            # posso retornar o passo para o normal
                            if not (first_fluxo and first_tensao) and minimal_step:
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
                                print("✅ Primeira violação de geração atingida, passo será reduzido.")
                                violou_geracao = False
                                # Retorno pro último valor de Pl e Ql antes da divergência e 
                                # diminuo o passo
                                Pl_old, Ql_old = Pl, Ql
                                Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                            # Se violou geração e já tive alguma violação (qualquer uma) não reduzo o passo
                            else:
                                first_geracao = True
                                print("✅ Primeira violação de geração atingida. Passo já está minimizado.")
                                violou_geracao = False
                            # Acrescento observação no ponto de primeira violação de geração
                            if observacao == '':
                                observacao = "Ponto da primeira violação de geração"
                            else:
                                observacao += " | Ponto da primeira violação de geração"
            # ---------------- ANÁLISE DE CONVERGÊNCIA ----------------
            # Se já divergiu eu não verifico violação.
            else:
                # Se já teve a primeira divergência, encerra o processo.
                if first_divergence:
                    print("✅ Ponto de divergência encontrado, processo será finalizado.")
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
                    break
                # Acrescento observação no ponto de primeira violação de geração
                if observacao == '':
                    observacao = "Ponto da primeira divergência"
                else:
                    observacao += " | Ponto da primeira divergência"
                # Se divergiu e ainda não tive nehuma primeira divergência, eu reduzo o passo
                if not minimal_step:
                    first_divergence = True
                    print("✅ Primeira divergência atingida, passo será reduzido.")
                    converged = True
                    # Retorno pro último valor de Pl e Ql antes da divergência e diminuo o passo
                    Pl_old, Ql_old = Pl, Ql
                    Pl, Ql, factor_P, factor_Q, minimal_step = reduce_step(Pl, Ql, factor_P, factor_Q, angulo, reduce)
                # Se divergiu e já tive alguma divergência, não reduzo o passo
                else:
                    first_divergence = True
                    print("✅ Primeira divergência atingida. Passo já está minimizado.")
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
    if minimal_step:
        # Fatores de aumento retornam ao original para o próximo ângulo
        factor_P *= reduce
        factor_Q *= reduce
        minimal_step = False
    # Retorna todas as flags para o ponto original True
    converged = True
    violou_tensao = False
    violou_fluxo = False
    violou_geracao = False
    first_divergence = False
    first_tensao = False
    first_fluxo = False
    first_geracao = False
    # Potência Ativa retorna à Original
    Pl = Pl_original
    # Potência Reativa retorna à Original
    Ql = Ql_original
exit_df = pd.DataFrame(exit_list)
nome_arquivo = os.path.splitext(os.path.basename(arquivo_pwf))[0]
arq_resultado = f"resultado_{nome_arquivo}.xlsx"
exit_df.to_excel(arq_resultado, index=False)

plot_df = pd.DataFrame(plot_list)
arq_plot = f"plot_{nome_arquivo}.xlsx"
plot_df.to_excel(arq_plot, index=False)

plot = PlotFlexibilidade(plot_df)

plot.gerar_relatorio()