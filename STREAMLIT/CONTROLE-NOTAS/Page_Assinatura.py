# Page_Assinatura.py
import streamlit as st
import pandas as pd
from datetime import datetime

from auth import force_relogin_on_navigate, add_logout_button


FILE_PATH = "STREAMLIT/CONTROLE-NOTAS/Notas.csv"
COLUNA_NF = "N NF"
COLUNA_FORNECEDOR = "FORNECEDOR"
COLUNA_VALOR = "Valor" 
COLUNA_VENC = "DT VENC"
COLUNA_GESTOR_RESP = 'GESTOR_RESP'
COLUNA_ASSINATURA = 'ASSINATURA'
COLUNA_GESTOR_ASSINATURA = 'GESTORASSINATURA'
COLUNA_ENTREGA = 'ENTREGA GESTOR'

# Colunas que o usuário não pode editar diretamente na tabela
COLUNAS_DESABILITADAS = (
    COLUNA_NF, 
    COLUNA_FORNECEDOR, 
    COLUNA_VALOR, 
    COLUNA_VENC, 
    COLUNA_GESTOR_RESP, 
    COLUNA_GESTOR_ASSINATURA,
    COLUNA_ENTREGA
)

# --- Funções de Manipulação de Dados (CSV) ---

@st.cache_data(ttl=300) # Cache de 5 minutos
def carregar_dados_csv(filepath=FILE_PATH):
    """
    Carrega e processa os dados do arquivo CSV.
    """
    try:
        df = pd.read_csv(filepath)

        # --- Conversão e Limpeza de Tipos ---
        # Converte a coluna de assinatura para booleano (True/False)
        if COLUNA_ASSINATURA in df.columns:
            df[COLUNA_ASSINATURA] = df[COLUNA_ASSINATURA].astype(str).str.upper().map({'TRUE': True, 'VERDADEIRO': True}).fillna(False).astype(bool)
        else:
            st.error(f"Erro Crítico: A coluna '{COLUNA_ASSINATURA}' não foi encontrada no arquivo CSV!")
            return None

        # Converte colunas de valores e datas, tratando possíveis erros
        if COLUNA_VALOR in df.columns:
            # Garante que a coluna seja string antes de usar '.str'
            df[COLUNA_VALOR] = pd.to_numeric(df[COLUNA_VALOR].astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
        
        # Converte colunas de data
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
    """
    Salva o DataFrame completo de volta para o arquivo CSV, formatando as colunas corretamente.
    """
    try:
        # Crie uma cópia para evitar alterar o DataFrame original no cache
        df_salvo = df_para_salvar.copy()

        # --- Formatação para Escrita no CSV ---
        # Converte booleano para 'TRUE'/'FALSE'
        if COLUNA_ASSINATURA in df_salvo.columns:
            df_salvo[COLUNA_ASSINATURA] = df_salvo[COLUNA_ASSINATURA].apply(lambda x: 'TRUE' if x else 'FALSE')

        # Formata datas para o padrão brasileiro, tratando valores nulos (NaT)
        if COLUNA_VENC in df_salvo.columns:
            df_salvo[COLUNA_VENC] = df_salvo[COLUNA_VENC].dt.strftime('%d/%m/%Y').fillna('')
        
        if COLUNA_ENTREGA in df_salvo.columns:
            df_salvo[COLUNA_ENTREGA] = df_salvo[COLUNA_ENTREGA].dt.strftime('%d/%m/%Y').fillna('')

        if COLUNA_GESTOR_ASSINATURA in df_salvo.columns:
            df_salvo[COLUNA_GESTOR_ASSINATURA] = df_salvo[COLUNA_GESTOR_ASSINATURA].dt.strftime('%d/%m/%Y %H:%M:%S').fillna('')
        
        # Salva o arquivo CSV com encoding UTF-8 e sem o index do pandas
        df_salvo.to_csv(filepath, index=False, encoding='utf-8')
        
        return True
    except Exception as e:
        st.error(f"Falha ao salvar o arquivo CSV: {e}")
        return False

# --- Lógica da Página ---

def show_pcm_page():
    """
    Mostra o conteúdo da página de Assinatura.
    """
    st.title("CONTROLE DE NOTAS :lower_left_fountain_pen:")
    st.markdown("Marque na coluna **Assinar?** e clique em **Salvar Alterações** para confirmar.")
    
    logged_in_user = st.session_state.get("logged_in_user", "Usuário Desconhecido")
    st.sidebar.success(f"Logado como: {logged_in_user}")
    add_logout_button()

    if st.button("🔄 Recarregar Dados"):
        carregar_dados_csv.clear() # Limpa o cache
        st.rerun()

    df_original = carregar_dados_csv()

    if df_original is None:
        st.warning("Não foi possível carregar os dados. Verifique os erros acima.")
        st.stop()

    if COLUNA_GESTOR_RESP not in df_original.columns:
        st.error(f"Erro Crítico: A coluna '{COLUNA_GESTOR_RESP}' não foi encontrada na planilha.")
        st.stop()

    # Filtra o DataFrame para mostrar apenas as notas do usuário logado
    df_filtrado_usuario = df_original[df_original[COLUNA_GESTOR_RESP] == logged_in_user].copy()

    if df_filtrado_usuario.empty:
        st.info(f"Nenhum registro de nota pendente encontrado para o gestor '{logged_in_user}'.")
        st.stop()

    st.subheader(f"Suas Notas Pendentes ({logged_in_user})")

    # Armazena o estado original do DF filtrado para comparação posterior
    st.session_state['df_antes_da_edicao'] = df_filtrado_usuario.copy()

    edited_df = st.data_editor(
        df_filtrado_usuario,
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

            # Compara o DF editado com o seu estado antes da edição
            for index, row in edited_df.iterrows():
                assinatura_antes = df_antes.loc[index, COLUNA_ASSINATURA]
                assinatura_agora = row[COLUNA_ASSINATURA]

                # Se o valor da checkbox mudou
                if assinatura_antes != assinatura_agora:
                    mudancas_detectadas = True
                    # Atualiza o valor da assinatura no DF completo
                    df_para_salvar.loc[index, COLUNA_ASSINATURA] = assinatura_agora
                    
                    # Se a caixa foi marcada, registra a data/hora atual
                    if assinatura_agora:
                        df_para_salvar.loc[index, COLUNA_GESTOR_ASSINATURA] = datetime.now()
                    # Se a caixa foi desmarcada, limpa a data/hora
                    else:
                        df_para_salvar.loc[index, COLUNA_GESTOR_ASSINATURA] = pd.NaT

            if not mudancas_detectadas:
                st.info("Nenhuma alteração foi feita.")
            # Salva o DataFrame completo e atualizado no CSV
            elif salvar_dados_csv(df_para_salvar):
                st.success("Alterações salvas com sucesso!")
                st.balloons()
                carregar_dados_csv.clear() # Limpa o cache para a próxima recarga
                st.rerun()
            else:
                st.error("Falha ao salvar as alterações no arquivo CSV.")

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao salvar: {e}")

# --- Execução Principal ---
if __name__ == "__main__":
    # Verifica se o usuário está logado
    if force_relogin_on_navigate(__file__):
        show_pcm_page()
    else:
        # A função de autenticação (se existir) deve cuidar da tela de login
        st.warning("Você precisa fazer login para acessar esta página.")
