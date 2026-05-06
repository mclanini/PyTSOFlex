from utils import *
import pandas as pd

target_bar = '14'
factor = 1.5
converged = True

#Leitura do PWF Original para verificação da linha de modificação

# Caminho do arquivo de entrada (.pwf)
arquivo_pwf = r"C:\Users\Usuario\Documents\Projeto Regiao Flexibilidade\PyTSOFlex\IEEE14_original.pwf"

# separa nome e extensão
base, ext = os.path.splitext(arquivo_pwf)

# cria novo nome
arquivo_pwf_modificado = f"{base}_modificado{ext}"

with open(arquivo_pwf) as f: 
    lines = f.readlines()
    target_line, Pl_original, Ql_original = check_line_pq(lines, target_bar)
    Pl = Pl_original
    Ql = Ql_original

# Modifica linha para salvar relatório e não sobrepor o original
lines = create_report(lines)

exit_list = []
iteracao = 1
exit_list.append({
    "Iteracao": iteracao,
    "Característica": "Original",
    "PL": f"{Pl:5.2f}"[:5],
    "QL": f"{Ql:5.2f}"[:5],
    "Convergiu": True
})

while converged == True:
    #Atualiza valores (em memória) de Pl e Ql
    Pl *= factor 
    Ql *= factor

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
    executed_2 = os.path.exists("RELAT_NEW.OUT")
    print(executed, executed_2)
    if not executed or not executed_2:
        print("❌ Falha ao executar o ANAREDE ou gerar o relatório.")
        break
    else:
        print("✅ ANAREDE executado e relatório gerado com sucesso.")
        # Lê o relatório para verificar convergência
        converged = check_convergence()
        if converged:
            print("🔄 Convergência atingida, aumentando carga...")
        else:
            print("✅ Convergência não atingida, processo finalizado.")
            iteracao += 1
            exit_list.append({
                "Iteracao": iteracao,
                "Característica": "Modificado",
                "PL": f"{Pl:5.2f}"[:5],
                "QL": f"{Ql:5.2f}"[:5],
                "Convergiu": converged
            })
            break
    iteracao += 1
    exit_list.append({
        "Iteracao": iteracao,
        "Característica": "Modificado",
        "PL": f"{Pl:5.2f}"[:5],
        "QL": f"{Ql:5.2f}"[:5],
        "Convergiu": converged
    })
exit_df = pd.DataFrame(exit_list)
exit_df.to_excel("resultado.xlsx", index=False)