import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import matplotlib.pyplot as plt
from io import BytesIO
from xhtml2pdf import pisa

# --- Configurações da Página ---
st.set_page_config(
    page_title="HT Gestão de Locação",
    page_icon="🚗",
    layout="wide"
)

# --- CONSTANTES DE ARQUIVOS ---
ARQUIVO_CLIENTES = "clientes.csv"
ARQUIVO_VEICULOS = "veiculos.csv"
ARQUIVO_FATURAS = "ultima_fatura.txt"
ARQUIVO_TRANSACOES = "transacoes.csv"

# --- FUNÇÃO PARA CONVERTER HTML PARA PDF ---
def convert_html_to_pdf(html_string):
    """Converte uma string HTML em um arquivo PDF em memória."""
    pdf_output = BytesIO()
    pisa_status = pisa.CreatePDF(
        BytesIO(html_string.encode("UTF-8")),
        dest=pdf_output,
        encoding='UTF-8'
    )
    if pisa_status.err:
        return None
    pdf_output.seek(0)
    return pdf_output

# --- Funções de Manipulação de Dados ---
def ler_ultimo_numero_fatura():
    try:
        with open(ARQUIVO_FATURAS, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def salvar_numero_fatura(numero_usado):
    with open(ARQUIVO_FATURAS, "w") as f:
        f.write(str(numero_usado))

def carregar_dados(nome_arquivo, colunas):
    if not os.path.exists(nome_arquivo):
        df = pd.DataFrame(columns=colunas)
        df.to_csv(nome_arquivo, index=False)
    # Conversores para garantir que colunas específicas sejam lidas como string
    converters = {
        'CPF/CNPJ': str,
        'CEP': str,
        'Placa': str,
        'Telefone': str
    }
    return pd.read_csv(nome_arquivo, converters=converters)

def salvar_dados(df, nome_arquivo):
    df.to_csv(nome_arquivo, index=False)

# Define as colunas para os arquivos CSV
colunas_clientes = ["Nome", "CPF/CNPJ", "Endereço", "Município", "UF", "CEP", "Telefone", "Email"]
colunas_veiculos = ["Placa", "Marca", "Modelo", "Ano", "Cor"]
colunas_transacoes = ["Placa", "Data", "Tipo", "Valor", "Categoria", "Descricao"]

# --- Páginas da Aplicação ---

def pagina_gerar_recibo_completa():
    st.header("Emitir Nova Fatura de Locação", divider='blue')

    df_clientes_atual = carregar_dados(ARQUIVO_CLIENTES, colunas_clientes)
    df_veiculos_atual = carregar_dados(ARQUIVO_VEICULOS, colunas_veiculos)

    if df_clientes_atual.empty or df_veiculos_atual.empty:
        st.warning("⚠ É necessário cadastrar pelo menos um cliente e um veículo.")
        return

    st.subheader("Informações da Fatura")

    ultimo_numero = ler_ultimo_numero_fatura()
    proximo_num_sugerido = ultimo_numero + 1

    col_num, col_data_emissao, col_vencimento = st.columns(3)
    with col_num:
        num_fatura_usado = st.number_input("Nº da Fatura", min_value=1, value=proximo_num_sugerido, step=1, help=f"O número sequencial sugerido é {proximo_num_sugerido}.")
    with col_data_emissao:
        data_emissao = st.date_input("Data da Emissão", datetime.today())
    with col_vencimento:
        data_vencimento = st.date_input("Data de Vencimento", datetime.today())

    st.subheader("Cliente e Veículo")
    col_cli, col_vei = st.columns(2)
    with col_cli:
        nomes_clientes = df_clientes_atual['Nome'].tolist()
        cliente_selecionado_nome = st.selectbox("Selecione o Cliente", options=nomes_clientes, index=None, placeholder="Escolha um cliente...")

    with col_vei:
        mapa_veiculos = {row['Placa']: f"{row['Placa']} ({row['Marca']} {row['Modelo']})" for index, row in df_veiculos_atual.iterrows()}
        opcoes_placas = list(mapa_veiculos.keys())
        placa_selecionada = st.selectbox("Selecione o Veículo", options=opcoes_placas, index=None, placeholder="Escolha um veículo...", format_func=lambda placa: mapa_veiculos.get(placa, "Veículo inválido"))

    if not cliente_selecionado_nome or not placa_selecionada:
        st.info("Por favor, selecione um cliente e um veículo para continuar.")
        return

    cliente_selecionado = df_clientes_atual[df_clientes_atual['Nome'] == cliente_selecionado_nome].iloc[0]
    veiculo_selecionado = df_veiculos_atual[df_veiculos_atual['Placa'] == placa_selecionada].iloc[0]

    st.subheader("Detalhes da Locação")
    col_periodo1, col_periodo2, col_contrato = st.columns(3)
    with col_periodo1:
        data_inicio_periodo = st.date_input("Início do Período da Locação", datetime.today())
    with col_periodo2:
        data_fim_periodo = st.date_input("Fim do Período da Locação", datetime.today())
    with col_contrato:
        contrato_str = st.text_input("Contrato (Ex: 1/12)", "1/12")

    desc_item = st.text_input("Descrição do Item principal", "Locação de Veículo")

    col_valor_str, col_valor_extenso = st.columns(2)
    with col_valor_str:
        valor_locacao_str = st.text_input("Valor Total da Fatura (R$)", "2.400,00")
    with col_valor_extenso:
        valor_por_extenso = st.text_input("Valor por Extenso", "Dois mil e quatrocentos reais")

    if st.button("Gerar Fatura", type="primary"):
        try:
            num_fatura = num_fatura_usado

            logo_html_tag = ""
            try:
                # Tenta carregar o logo a partir do diretório atual
                logo_path = "logo.png"
                if os.path.exists(logo_path):
                    with open(logo_path, "rb") as f:
                        logo_data = f.read()
                        logo_base64 = base64.b64encode(logo_data).decode("utf-8")
                        logo_html_tag = f'<img src="data:image/png;base64,{logo_base64}" class="logo">'
            except Exception:
                logo_html_tag = "" # Se der erro, não exibe o logo

            html_recibo = f"""
            <!DOCTYPE html><html lang="pt-BR"><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="UTF-8"><title>Fatura de Locação N° {num_fatura}</title>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 12px; color: #000; background-color: #fff; }} .container {{ max-width: 800px; margin: auto; border: 1px solid #000; padding: 40px; background-color: #fff; }} .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #000; padding-bottom: 10px;}} .logo-empresa-container {{ flex: 2; display: flex; align-items: center; }} .logo {{ max-height: 70px; width: auto; margin-right: 15px; }} .empresa-info p {{ margin: 3px 0; }} .fatura-box {{ flex: 1; border: 1px solid #000; padding: 5px; text-align: center; }} .fatura-box h2 {{ margin: 0; font-size: 14px; }} .fatura-box p {{ margin: 2px 0; }} .sacado-box {{ border: 1px solid #000; padding: 10px; margin-top: 10px; }} .sacado-box p {{ margin: 3px 0; }} .vencimento-box {{ border: 1px solid #000; padding: 5px; margin-top: 10px; display: flex; justify-content: space-between; }} .vencimento-box div {{ width: 50%; }} .extenso-box {{ border: 1px solid #000; padding: 5px; margin-top: 10px; }} .descricao-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }} .descricao-table th, .descricao-table td {{ border: 1px solid #000; padding: 5px; }} .descricao-table th {{ text-align: center; }} .descricao-table .valor-col {{ text-align: right; width: 120px; }} .descricao-table .total-label {{ text-align: right; font-weight: bold; border-left: none; border-bottom: none;}} .footer {{ text-align: center; margin-top: 15px; font-size: 10px; }} strong {{ font-weight: bold; }} @media print {{ @page {{ size: A4; margin: 20mm; }} body {{ margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }} .container {{ border: none; box-shadow: none; width: 100%; max-width: 100%; margin: 0; padding: 0; }} }}
            </style></head>
            <body><div class="container">
                <div class="header"><div class="logo-empresa-container">{logo_html_tag}<div class="empresa-info"><strong>HT Locações Auto LTDA</strong><p>Rua dos Contabilistas, 184 - PASSOS/MG CEP 37900-114</p><p>CNPJ: 05.261.064/0001-60</p><p>FONE: (35)999817121</p></div></div><div class="fatura-box"><h2>FATURA DE LOCAÇÃO</h2><p><strong>N°:</strong> {num_fatura}</p><p><strong>Data da Emissão:</strong> {data_emissao.strftime('%d/%m/%Y')}</p></div></div>
                <div class="sacado-box"><p><strong>Sacado:</strong> {cliente_selecionado['Nome']}</p><p><strong>Endereço:</strong> {cliente_selecionado['Endereço']}</p><p><strong>Município:</strong> {cliente_selecionado['Município']} <strong>UF:</strong> {cliente_selecionado['UF']} <strong>CEP:</strong> {cliente_selecionado['CEP']}</p><p><strong>CNPJ(MF)/CPF:</strong> {cliente_selecionado['CPF/CNPJ']}</p></div>
                <div class="vencimento-box"><div><strong>Fatura/Duplicata Valor R$:</strong> {valor_locacao_str}</div><div><strong>Vencimento(s):</strong> {data_vencimento.strftime('%d/%m/%Y')}</div></div>
                <div class="extenso-box"><strong>Valor por Extenso:</strong> {valor_por_extenso}</div>
                <table class="descricao-table"><thead><tr><th>Descrição</th><th>Valor R$</th></tr></thead><tbody>
                <tr><td>Contrato: {contrato_str} Período: {data_inicio_periodo.strftime('%d/%m/%Y')} a {data_fim_periodo.strftime('%d/%m/%Y')}<br>Placa Atual: {veiculo_selecionado['Placa']}<br>Itens/Despesas e Serviços Adicionais:<br>{desc_item} - R$ {valor_locacao_str}</td><td class="valor-col">{valor_locacao_str}</td></tr>
                <tr><td class="total-label">Total da Fatura</td><td class="valor-col"><strong>R$ {valor_locacao_str}</strong></td></tr>
                </tbody></table><div class="footer"><p>Atividade não sujeita ao ISSQN e à emissão de NF conforme Lei 116/03 - Item 3.01</p></div>
            </div></body></html>
            """

            st.subheader("Pré-visualização da Fatura", divider='blue')
            st.components.v1.html(html_recibo, height=600, scrolling=True)

            pdf_file = convert_html_to_pdf(html_recibo)
            if pdf_file:
                st.download_button(
                    label="📄 Baixar Recibo (PDF)",
                    data=pdf_file,
                    file_name=f"fatura_{num_fatura}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Ocorreu um erro ao gerar o PDF do recibo.")

            valor_float = float(valor_locacao_str.replace('.', '').replace(',', '.'))
            nova_transacao = pd.DataFrame([{
                "Placa": placa_selecionada,
                "Data": data_emissao.strftime('%Y-%m-%d'),
                "Tipo": "Entrada",
                "Valor": valor_float,
                "Categoria": "Aluguel",
                "Descricao": f"Fatura Nº {num_fatura} - Cliente: {cliente_selecionado_nome}"
            }])
            df_transacoes_atual = carregar_dados(ARQUIVO_TRANSACOES, colunas_transacoes)
            df_transacoes_final = pd.concat([df_transacoes_atual, nova_transacao], ignore_index=True)
            salvar_dados(df_transacoes_final, ARQUIVO_TRANSACOES)

            if num_fatura_usado > ultimo_numero:
                salvar_numero_fatura(num_fatura_usado)

            st.success(f"Fatura Nº {num_fatura_usado} gerada e transação registrada na Gestão de Frotas!")

        except Exception as e:
            st.error(f"Erro ao processar a fatura: {e}")

def pagina_gestao_frotas_completa():
    st.header("Gestão Financeira da Frota", divider='orange')

    df_veiculos = carregar_dados(ARQUIVO_VEICULOS, colunas_veiculos)
    df_transacoes = carregar_dados(ARQUIVO_TRANSACOES, colunas_transacoes)

    if df_veiculos.empty:
        st.warning("Nenhum veículo cadastrado. Por favor, cadastre um veículo primeiro.")
        return

    mapa_veiculos = {row['Placa']: f"{row['Placa']} ({row['Marca']} {row['Modelo']})" for index, row in df_veiculos.iterrows()}
    placa_selecionada = st.selectbox(
        "Selecione um Veículo para Análise",
        options=list(mapa_veiculos.keys()),
        format_func=lambda placa: mapa_veiculos.get(placa, "Veículo inválido"),
        index=None,
        placeholder="Escolha um veículo..."
    )

    if placa_selecionada:
        veiculo_info = df_veiculos[df_veiculos['Placa'] == placa_selecionada].iloc[0]
        st.subheader(f"Detalhes do Veículo: {veiculo_info['Marca']} {veiculo_info['Modelo']} - {veiculo_info['Placa']}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Ano", veiculo_info['Ano'])
        col2.metric("Cor", veiculo_info['Cor'])

        st.subheader("Histórico de Transações")
        transacoes_veiculo = df_transacoes[df_transacoes['Placa'] == placa_selecionada].copy()
        
        if not transacoes_veiculo.empty:
            transacoes_veiculo['Data'] = pd.to_datetime(transacoes_veiculo['Data'])
            transacoes_veiculo = transacoes_veiculo.sort_values(by='Data', ascending=False)
            
            st.dataframe(transacoes_veiculo.style.format({'Valor': 'R$ {:,.2f}'}), use_container_width=True)

            # Resumo Financeiro
            total_entradas = transacoes_veiculo[transacoes_veiculo['Tipo'] == 'Entrada']['Valor'].sum()
            total_saidas = transacoes_veiculo[transacoes_veiculo['Tipo'] == 'Saída']['Valor'].sum()
            balanco = total_entradas - total_saidas

            st.subheader("Resumo Financeiro")
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("Total de Receitas", f"R$ {total_entradas:,.2f}")
            col_res2.metric("Total de Despesas", f"R$ {total_saidas:,.2f}")
            col_res3.metric("Balanço", f"R$ {balanco:,.2f}")

            # Gráfico
            st.subheader("Gráfico de Balanço Mensal")
            transacoes_veiculo['Mes'] = transacoes_veiculo['Data'].dt.to_period('M')
            balanco_mensal = transacoes_veiculo.groupby('Mes').apply(
                lambda x: x[x['Tipo'] == 'Entrada']['Valor'].sum() - x[x['Tipo'] == 'Saída']['Valor'].sum()
            ).reset_index(name='Balanço')
            balanco_mensal['Mes'] = balanco_mensal['Mes'].astype(str)

            fig, ax = plt.subplots()
            ax.bar(balanco_mensal['Mes'], balanco_mensal['Balanço'], color=['#28a745' if b >= 0 else '#dc3545' for b in balanco_mensal['Balanço']])
            ax.set_ylabel('Balanço (R$)')
            ax.set_xlabel('Mês')
            ax.set_title('Balanço Financeiro Mensal do Veículo')
            plt.xticks(rotation=45)
            st.pyplot(fig)

        else:
            st.info("Nenhuma transação registrada para este veículo.")

        # Adicionar nova transação
        with st.expander("➕ Adicionar Nova Transação Manual"):
            with st.form("nova_transacao_form", clear_on_submit=True):
                tipo_transacao = st.selectbox("Tipo de Transação", ["Entrada", "Saída"])
                data_transacao = st.date_input("Data", datetime.today())
                valor_transacao = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                categoria_transacao = st.text_input("Categoria", "Manutenção")
                descricao_transacao = st.text_area("Descrição")
                
                submitted = st.form_submit_button("Registrar Transação")
                if submitted:
                    nova_transacao = pd.DataFrame([{
                        "Placa": placa_selecionada,
                        "Data": data_transacao.strftime('%Y-%m-%d'),
                        "Tipo": tipo_transacao,
                        "Valor": valor_transacao,
                        "Categoria": categoria_transacao,
                        "Descricao": descricao_transacao
                    }])
                    df_transacoes_final = pd.concat([df_transacoes, nova_transacao], ignore_index=True)
                    salvar_dados(df_transacoes_final, ARQUIVO_TRANSACOES)
                    st.success("Transação registrada com sucesso!")
                    st.rerun()

def pagina_cadastrar_cliente_completa():
    st.header("Cadastro de Clientes", divider='green')
    
    with st.form("form_cliente", clear_on_submit=True):
        st.subheader("Informações do Cliente")
        nome = st.text_input("Nome Completo ou Razão Social")
        cpf_cnpj = st.text_input("CPF ou CNPJ")
        endereco = st.text_input("Endereço (Rua, Número, Bairro)")
        col1, col2, col3 = st.columns(3)
        with col1:
            municipio = st.text_input("Município")
        with col2:
            uf = st.text_input("UF", max_chars=2)
        with col3:
            cep = st.text_input("CEP")
        
        col_tel, col_email = st.columns(2)
        with col_tel:
            telefone = st.text_input("Telefone")
        with col_email:
            email = st.text_input("E-mail")

        submitted = st.form_submit_button("Cadastrar Cliente")
        if submitted:
            if nome and cpf_cnpj:
                novo_cliente = pd.DataFrame([{
                    "Nome": nome, "CPF/CNPJ": cpf_cnpj, "Endereço": endereco,
                    "Município": municipio, "UF": uf.upper(), "CEP": cep,
                    "Telefone": telefone, "Email": email
                }])
                df_clientes_atual = carregar_dados(ARQUIVO_CLIENTES, colunas_clientes)
                df_clientes_final = pd.concat([df_clientes_atual, novo_cliente], ignore_index=True)
                salvar_dados(df_clientes_final, ARQUIVO_CLIENTES)
                st.success(f"Cliente '{nome}' cadastrado com sucesso!")
            else:
                st.error("Nome e CPF/CNPJ são campos obrigatórios.")

    st.subheader("Clientes Cadastrados")
    df_clientes = carregar_dados(ARQUIVO_CLIENTES, colunas_clientes)
    st.dataframe(df_clientes, use_container_width=True)

def pagina_cadastrar_veiculo_completa():
    st.header("Cadastro de Veículos", divider='red')

    with st.form("form_veiculo", clear_on_submit=True):
        st.subheader("Informações do Veículo")
        placa = st.text_input("Placa do Veículo")
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        col1, col2 = st.columns(2)
        with col1:
            ano = st.number_input("Ano", min_value=1980, max_value=datetime.now().year + 1, step=1, value=datetime.now().year)
        with col2:
            cor = st.text_input("Cor")

        submitted = st.form_submit_button("Cadastrar Veículo")
        if submitted:
            if placa and marca and modelo:
                novo_veiculo = pd.DataFrame([{
                    "Placa": placa.upper(), "Marca": marca, "Modelo": modelo,
                    "Ano": ano, "Cor": cor
                }])
                df_veiculos_atual = carregar_dados(ARQUIVO_VEICULOS, colunas_veiculos)
                df_veiculos_final = pd.concat([df_veiculos_atual, novo_veiculo], ignore_index=True)
                salvar_dados(df_veiculos_final, ARQUIVO_VEICULOS)
                st.success(f"Veículo com placa '{placa.upper()}' cadastrado com sucesso!")
            else:
                st.error("Placa, Marca e Modelo são campos obrigatórios.")

    st.subheader("Veículos Cadastrados")
    df_veiculos = carregar_dados(ARQUIVO_VEICULOS, colunas_veiculos)
    st.dataframe(df_veiculos, use_container_width=True)

# --- NAVEGAÇÃO PRINCIPAL ---
st.sidebar.title("Navegação Principal")
paginas = {
    "📄 Gerar Fatura": pagina_gerar_recibo_completa,
    "📊 Gestão de Frotas": pagina_gestao_frotas_completa,
    "👤 Cadastrar Cliente": pagina_cadastrar_cliente_completa,
    "🚗 Cadastrar Veículo": pagina_cadastrar_veiculo_completa
}

pagina_selecionada = st.sidebar.radio("Escolha uma página", list(paginas.keys()))

# Executa a função da página selecionada
paginas[pagina_selecionada]()
