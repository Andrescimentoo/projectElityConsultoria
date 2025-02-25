import tkinter as tk
import winsound
from tkinter import messagebox, scrolledtext
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pyperclip  # Para copiar resultados para a área de transferência
import requests
import re
import undetected_chromedriver as uc
import time
import keyboard  # Para atalhos globais

# Variável global para gerenciar o navegador
driver = None
contador_lojas = 0  # Contador de lojas processadas

def inicializar_driver():
    global driver
    if driver is None:
        driver = uc.Chrome()  # Inicializa o navegador uma vez
    return driver

def fechar_driver():
    global driver
    if driver:
        driver.quit()
        driver = None

def fechar_anuncio(driver):
    try:
        fechar_anuncio_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//svg[@viewBox='0 0 48 48' and @fill='#5F6368']/parent::button"))
        )
        fechar_anuncio_button.click()
    except Exception as e:
        print("Nenhum anúncio encontrado ou erro ao fechar o anúncio:", e)

def tentar_n_vezes(func, max_tentativas, *args, **kwargs):
    """Função genérica para tentar executar outra função um número máximo de vezes."""
    for tentativa in range(max_tentativas):
        resultado = func(*args, **kwargs)
        if resultado:
            return resultado
        print(f"Tentativa {tentativa + 1} falhou.")
        time.sleep(1)  # Espera 1 segundo antes da próxima tentativa
    return None

def obter_dados_ifood(link_loja):
    try:
        response = requests.get(link_loja)
        if response.status_code == 200:
            conteudo = response.text

            nome_loja_match = re.search(r'<h1 class="merchant-info__title">(.*?)</h1>', conteudo)
            nome_loja = nome_loja_match.group(1) if nome_loja_match else None

            cnpj_match = re.search(r'"type":"CNPJ","value":"(\d{14,18})"', conteudo)
            cnpj = cnpj_match.group(1) if cnpj_match else None

            print(f"CNPJ capturado: {cnpj}")  # Debug para verificar o CNPJ capturado
            return nome_loja, cnpj
        else:
            print(f"Erro ao acessar a página. Status: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Erro ao acessar a página: {e}")
        return None, None

def obter_dados_casa_dados(cnpj):
    print(cnpj)
    try:
        driver = inicializar_driver()  # Reutiliza o navegador existente

        for tentativa in range(7):
            try:
                url = f"https://casadosdados.com.br/solucao/cnpj/{cnpj}"
                driver.get(url)

                # Verifica se a página retornou um erro 403 ou similar
                if "403 Forbidden" in driver.page_source or "404" in driver.title.lower():
                    print(f"Erro detectado na tentativa {tentativa + 1}. Recarregando página.")
                    driver.refresh()
                    time.sleep(1)  # Aguarda um curto intervalo antes de tentar novamente
                    continue

                # Captura o HTML imediatamente
                html = driver.page_source

                # Processa o HTML com BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')

                # Busca os dados usando seletores do BeautifulSoup
                razao_social = soup.find('label', text='Razão Social:').find_next('p').text.strip()
                telefones = [a['href'].replace('tel:', '') for a in soup.find_all('a', href=True) if 'tel:' in a['href']]

                return razao_social, telefones

            except Exception as e:
                print(f"Erro ao acessar a página da Casa dos Dados na tentativa {tentativa + 1}: {e}")
                time.sleep(1)  # Aguarda antes de tentar novamente

        print("Falha ao obter os dados após 7 tentativas.")
        messagebox.showerror("Erro", "Não foi possível obter os dados da Casa dos Dados após 7 tentativas.")
        return None, []

    except Exception as e:
        print(f"Erro geral ao acessar Casa dos Dados: {e}")
        return None, []

def processar_loja_ifood():
    global contador_lojas
    start_time = time.time()  # Inicia o cronômetro

    link_loja_ifood = entry.get().strip()
    resultado_text.config(state=tk.NORMAL)
    resultado_text.delete(1.0, tk.END)
    loading_label.config(text="Buscando, espere enquanto conseguimos os dados...")
    loading_label.pack()

    if not link_loja_ifood.startswith("http://") and not link_loja_ifood.startswith("https://"):
        if not link_loja_ifood.startswith("www."):
            link_loja_ifood = "https://" + link_loja_ifood
        else:
            link_loja_ifood = "https://" + link_loja_ifood

    if "ifood.com.br" not in link_loja_ifood:
        loading_label.pack_forget()
        messagebox.showerror("Erro", "Por favor, insira um link válido do iFood.")
        return

    nome_loja, cnpj = tentar_n_vezes(obter_dados_ifood, 5, link_loja_ifood)

    if nome_loja:
        if cnpj:
            razao_social, telefones = obter_dados_casa_dados(cnpj)  # Chama a função com tentativas múltiplas
            if telefones:  # Incrementa o contador apenas se telefones forem encontrados
                contador_lojas += 1
                contador_label.config(text=f"Lojas Processadas: {contador_lojas}")
        else:
            messagebox.showerror("Erro", "CNPJ não encontrado após 5 tentativas.")
            razao_social, telefones = None, []

        link_simplificado = link_loja_ifood.replace("https://", "")

        result = (
            f"Nome da Loja: {nome_loja if nome_loja else 'Nome não encontrado.'}\n\n"
            f"Razão Social: {razao_social if razao_social else 'Razão social não encontrada.'}\n\n"
            f"Telefones: {', '.join(telefones) if telefones else 'Nenhum telefone encontrado.'}\n\n"
            f"Link simplificado: {link_simplificado}\n\n"
            f"Olá! Sou especialista em gestão de iFood e identifiquei várias melhorias que têm grande potencial de aumentar o desempenho e os lucros da sua loja. Estou falando com o dono do Delivery {nome_loja}?\n\n"
            f"__________________"
        )
        resultado_text.insert(tk.END, result, winsound.Beep(1000, 500))
        cnpj_label.config(text=f"CNPJ Encontrado: {cnpj}")  # Exibe o CNPJ capturado
    else:
        messagebox.showerror("Erro", "Falhou ao buscar os dados após 5 tentativas.")

    end_time = time.time()  # Finaliza o cronômetro
    duration = end_time - start_time
    timer_label.config(text=f"Tempo decorrido: {duration:.2f} segundos")

    loading_label.pack_forget()

def colar_na_barra(event=None):
    entry.focus_set()  # Define o foco na barra de entrada
    entry.delete(0, tk.END)  # Limpa o conteúdo atual
    entry.insert(0, pyperclip.paste())  # Cola o conteúdo copiado

def copiar_resultados():
    resultados = resultado_text.get(1.0, tk.END)
    pyperclip.copy(resultados.strip())

def aumentar_contador():
    global contador_lojas
    contador_lojas += 1
    contador_label.config(text=f"Lojas Processadas: {contador_lojas}")

def diminuir_contador():
    global contador_lojas
    if contador_lojas > 0:
        contador_lojas -= 1
        contador_label.config(text=f"Lojas Processadas: {contador_lojas}")

def restaurar_janela():
    root.deiconify()  # Restaura a janela se minimizada
    root.lift()       # Traz a janela para o topo
    root.focus_force()  # Força o foco na janela
    root.attributes("-topmost", True)  # Garante que ficará sobre outros apps
    root.attributes("-topmost", False)  # Remove o comportamento de "sempre no topo"

root = tk.Tk()
root.title("Consulta de Loja iFood")

# Inicializa o driver assim que o programa é iniciado
inicializar_driver()

# Frame para entrada e botão "Consultar"
entry_frame = tk.Frame(root)
entry_frame.pack(pady=10)

entry = tk.Entry(entry_frame, width=50)
entry.pack(side=tk.LEFT, padx=5)
entry.bind("<space>", lambda event: processar_loja_ifood())  # Ativa consulta com Space

processar_button = tk.Button(entry_frame, text="Consultar", command=processar_loja_ifood)
processar_button.pack(side=tk.LEFT)

# Frame para contador de lojas
contador_frame = tk.Frame(root)
contador_frame.pack(pady=5)

contador_label = tk.Label(contador_frame, text="Lojas Processadas: 0", fg="purple")
contador_label.pack(side=tk.LEFT, padx=5)

incrementar_button = tk.Button(contador_frame, text="+1 Loja", command=aumentar_contador)
incrementar_button.pack(side=tk.LEFT, padx=5)

decrementar_button = tk.Button(contador_frame, text="-1 Loja", command=diminuir_contador)
decrementar_button.pack(side=tk.LEFT, padx=5)

# Labels de status e informações
cnpj_label = tk.Label(root, text="CNPJ Encontrado: -", fg="green")
cnpj_label.pack(pady=5)

timer_label = tk.Label(root, text="Tempo decorrido: -", fg="blue")
timer_label.pack(pady=5)

# Botão de copiar resultados
copiar_button = tk.Button(root, text="Copiar Resultados", command=copiar_resultados)
copiar_button.pack(pady=5)

# Área de resultados
resultado_text = scrolledtext.ScrolledText(root, width=60, height=15, wrap=tk.WORD, state=tk.DISABLED)
resultado_text.pack(pady=10)

loading_label = tk.Label(root, text="", fg="blue")
loading_label.pack()

# Atalhos globais
keyboard.add_hotkey("F2", restaurar_janela)  # Atalho para restaurar a janela
root.bind("<Control-x>", lambda event: copiar_resultados())  # Atalho para copiar resultados
root.bind("<Control-v>", colar_na_barra) # Associa Ctrl+V para colar diretamente na barra de entrada

# Garante o fechamento do driver ao sair
import atexit
atexit.register(fechar_driver)

root.mainloop()
