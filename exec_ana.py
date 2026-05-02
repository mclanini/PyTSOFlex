import subprocess
import time
import psutil
import os

# Caminho completo do executável
caminho_exe = r"C:\CEPEL\Anarede\V120001\\Anarede.exe"

# Caminho do arquivo de entrada (.pwf)
arquivo_pwf = r"C:\Users\Usuario\Documents\Projeto Regiao Flexibilidade\IEEE14.pwf"

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
