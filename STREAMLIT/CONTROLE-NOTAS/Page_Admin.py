import streamlit as st
import pandas as pd
from datetime import datetime


from auth import force_relogin_on_navigate, add_logout_button


FILE_PATH = "Notas.csv"
COLUNA_NF = "N NF"
COLUNA_FORNECEDOR = "FORNECEDOR"
COLUNA_VALOR = "Valor" 
COLUNA_VENC = "DT VENC"
COLUNA_GESTOR_RESP = 'GESTOR_RESP'
COLUNA_ASSINATURA = 'ASSINATURA'
COLUNA_GESTOR_ASSINATURA = 'GESTORASSINATURA'
COLUNA_ENTREGA = 'ENTREGA GESTOR'
COLUNA_DEVOLUCAO = 'DEVOLUCAO'
COLUNA_DATA_DEVOLUCAO = 'DATA DEVOLUCAO'

ADM_USERNAME = "admin"

COLUNAS_DESABILITADAS = (
    COLUNA_NF, 
    COLUNA_FORNECEDOR, 
    COLUNA_VALOR, 
    COLUNA_VENC, 
    COLUNA_GESTOR_RESP, 
    COLUNA_GESTOR_ASSINATURA,
    COLUNA_ENTREGA
)

@st.cache_data(ttl=300) 
def carregar_dados_csv(filepath=FILE_PATH):
    try:
        df = pd.read_csv(filepath)

        if COLUNA_ASSINATURA in df.columns:
            df[COLUNA_ASSINATURA] = df[COLUNA_ASSINATURA].astype(str).str.upper().map({'TRUE': True, 'VERDADEIRO': True}).fillna(False).astype(bool)
        else:
            st.error(f"Erro Crítico: A coluna '{COLUNA_ASSINATURA}' não foi encontrada no arquivo CSV!")
            return None

        if COLUNA_VALOR in df.columns:

            df[COLUNA_VALOR] = pd.to_numeric(df[COLUNA_VALOR].astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
        

        date_columns = [COLUNA_VENC, COLUNA_ENTREGA, COLUNA_GESTOR_ASSINATURA]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{filepath}' não foi encontrado. Verifique se ele está no mesmo diretório do script.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return None


def salvar_dados_csv(df_para_salvar, filepath=FILE_PATH):

    try:
        df_salvo = df_para_salvar.copy()

        if COLUNA_ASSINATURA in df_salvo.columns:
            df_salvo[COLUNA_ASSINATURA] = df_salvo[COLUNA_ASSINATURA].apply(lambda x: 'TRUE' if x else 'FALSE')


        if COLUNA_VENC in df_salvo.columns:
            df_salvo[COLUNA_VENC] = df_salvo[COLUNA_VENC].dt.strftime('%d/%m/%Y').fillna('')
        
        if COLUNA_ENTREGA in df_salvo.columns:
            df_salvo[COLUNA_ENTREGA] = df_salvo[COLUNA_ENTREGA].dt.strftime('%d/%m/%Y').fillna('')

        if COLUNA_GESTOR_ASSINATURA in df_salvo.columns:
            df_salvo[COLUNA_GESTOR_ASSINATURA] = df_salvo[COLUNA_GESTOR_ASSINATURA].dt.strftime('%d/%m/%Y %H:%M:%S').fillna('')
        

        df_salvo.to_csv(filepath, index=False, encoding='utf-8')
        
        return True
    except Exception as e:
        st.error(f"Falha ao salvar o arquivo CSV: {e}")
        return False

# --- Lógica da Página PCM ---

def show_pcm_page_1():
    st.title("PAINEL DO ADMINISTRADOR - CONTROLE DE NOTAS ⚙️📝")
    
    


    df_original = carregar_dados_csv()
    if df_original is None: st.stop()

    st.subheader("Visão Geral - Todas as Notas")
    
    # Lista de gestores para o Selectbox, incluindo um valor em branco para novas notas
    lista_gestores = sorted([g for g in df_original[COLUNA_GESTOR_RESP].unique() if pd.notna(g)])

    edited_df = st.data_editor(
        df_original,
        disabled=COLUNAS_DESABILITADAS,
        num_rows="dynamic", # Permite ao ADM adicionar e remover linhas
        use_container_width=True,
        key="editor_adm",
        column_config={
            COLUNA_ASSINATURA: st.column_config.CheckboxColumn("Assinado?", default=False),
            COLUNA_DEVOLUCAO: st.column_config.CheckboxColumn("Devolvido?", default=False), # Rótulo corrigido
            COLUNA_VALOR: st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            COLUNA_VENC: st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            COLUNA_ENTREGA: st.column_config.DateColumn("Entrega Gestor", format="DD/MM/YYYY"), # Rótulo corrigido
            COLUNA_GESTOR_RESP: st.column_config.SelectboxColumn(
                "Gestor Responsável",
                options=lista_gestores,
                required=True, # Garante que o ADM sempre preencha
            )
        }
    )

    if st.button("Salvar Alterações do ADM", type="primary"):
        try:
            # Validação: Verifica se alguma linha nova está sem gestor responsável
            if edited_df[COLUNA_GESTOR_RESP].isnull().any() or (edited_df[COLUNA_GESTOR_RESP] == '').any():
                st.error("ERRO: Existem linhas sem 'Gestor Responsável' definido. Preencha antes de salvar.")
            else:
                df_para_salvar = edited_df.copy()
                
                # Lógica para atualizar data de assinatura e devolução
                for index, row in df_para_salvar.iterrows():
                    # Verifica se a linha existia antes para poder comparar
                    if index in df_original.index:
                        # Compara o estado da assinatura
                        if row[COLUNA_ASSINATURA] and not df_original.loc[index, COLUNA_ASSINATURA]:
                            df_para_salvar.loc[index, COLUNA_GESTOR_ASSINATURA] = datetime.now()
                        elif not row[COLUNA_ASSINATURA] and df_original.loc[index, COLUNA_ASSINATURA]:
                            df_para_salvar.loc[index, COLUNA_GESTOR_ASSINATURA] = pd.NaT # Limpa a data

                        # Compara o estado da devolução
                        if row[COLUNA_DEVOLUCAO] and not df_original.loc[index, COLUNA_DEVOLUCAO]:
                             df_para_salvar.loc[index, COLUNA_DATA_DEVOLUCAO] = datetime.now()
                        elif not row[COLUNA_DEVOLUCAO] and df_original.loc[index, COLUNA_DEVOLUCAO]:
                            df_para_salvar.loc[index, COLUNA_DATA_DEVOLUCAO] = pd.NaT # Limpa a data
                
                if salvar_dados_csv(df_para_salvar):
                    st.success("Alterações salvas com sucesso!")
                    st.balloons()
                    carregar_dados_csv.clear()
                    st.rerun()
        except Exception as e:
            st.error(f"Ocorreu um erro ao salvar: {e}")

def show_pcm_page_2():

    st.title("CONTROLE DE NOTAS :lower_left_fountain_pen:")
    st.markdown("Marque na coluna **Assinar?** e clique em **Salvar Alterações** para confirmar.")
    
    logged_in_user = st.session_state.get("logged_in_user", "Usuário Desconhecido")
    st.sidebar.success(f"Logado como: {logged_in_user}")
    
    df_original = carregar_dados_csv()

    if df_original is None:
        st.warning("Não foi possível carregar os dados. Verifique os erros acima.")
        st.stop()

    if COLUNA_GESTOR_RESP not in df_original.columns:
        st.error(f"Erro Crítico: A coluna '{COLUNA_GESTOR_RESP}' não foi encontrada na planilha.")
        st.stop()




    st.session_state['df_antes_da_edicao'] = df_original.copy()

    edited_df = st.data_editor(
        df_original,
        disabled=COLUNAS_DESABILITADAS,
        key=f"editor_notas_{logged_in_user}",
        use_container_width=True,
        column_config={
            COLUNA_ASSINATURA: st.column_config.CheckboxColumn("Assinar?", default=False),
            COLUNA_GESTOR_RESP: st.column_config.TextColumn("Gestor"),
            COLUNA_FORNECEDOR: st.column_config.TextColumn("Fornecedor"),
            COLUNA_NF: st.column_config.TextColumn("Nr NF"),
            COLUNA_VALOR: st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            COLUNA_VENC: st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            COLUNA_ENTREGA: st.column_config.DateColumn("Entrega", format="DD/MM/YYYY"),
            COLUNA_GESTOR_ASSINATURA: st.column_config.DatetimeColumn("Data Assinatura", format="DD/MM/YYYY HH:mm:ss"),
        }
    )

    if st.button("Salvar Alterações", type="primary"):
        try:
            df_antes = st.session_state['df_antes_da_edicao']
            df_para_salvar = df_original.copy()
            mudancas_detectadas = False


            for index, row in edited_df.iterrows():
                assinatura_antes = df_antes.loc[index, COLUNA_DEVOLUCAO]
                assinatura_agora = row[COLUNA_DEVOLUCAO]

                if assinatura_antes != assinatura_agora:
                    mudancas_detectadas = True

                    df_para_salvar.loc[index, COLUNA_DEVOLUCAO] = assinatura_agora

                    if assinatura_agora:
                        df_para_salvar.loc[index, COLUNA_DATA_DEVOLUCAO] = datetime.now()

                    else:
                        df_para_salvar.loc[index, COLUNA_DATA_DEVOLUCAO] = pd.NaT

            if not mudancas_detectadas:
                st.info("Nenhuma alteração foi feita.")

            elif salvar_dados_csv(df_para_salvar):
                st.success("Alterações salvas com sucesso!")
                st.balloons()
                carregar_dados_csv.clear() 
                st.rerun()
            else:
                st.error("Falha ao salvar as alterações no arquivo CSV.")

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao salvar: {e}")

# --- Execução Principal da Página ---

# Chama a função de verificação no início
if force_relogin_on_navigate(__file__):
    # Se logado, verifica se é o ADM
    logged_in_user = st.session_state.get("logged_in_user")
    if logged_in_user == ADM_USERNAME:
        # É ADM, mostra a página
        tab1, tab2 = st.tabs(["DEVOLUÇÃO", "GERAL"])
        with tab1:
            show_pcm_page_2()
        with tab2:
            show_pcm_page_1()
            
    else:
        # Não é ADM, mostra erro
        st.error("🚫 Acesso Negado!")
        st.warning(f"O usuário '{logged_in_user}' não tem permissão para acessar esta página.")
        st.info("Esta funcionalidade é restrita aos administradores.")
        add_logout_button() # Permite sair mesmo se negado
else:
    # Se não logado, a função 'check_password' já exibirá o formulário.
    st.warning("Você precisa fazer login como administrador para acessar esta página.")