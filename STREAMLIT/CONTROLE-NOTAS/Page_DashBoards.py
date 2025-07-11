import streamlit as st
import pandas as pd
from datetime import datetime
import os.path
import plotly.express as px
import plotly.graph_objects as go


from auth import force_relogin_on_navigate, add_logout_button


template_3 = dict(
layout=go.Layout(
    font=dict(family="Verdana", size=12, color="#333333"),
    title_font=dict(family="Verdana", size=24, color="#0c162c"),    
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f9f9f9",
    xaxis=dict(
        gridcolor="#e0e0e0",
        title_font=dict(size=14, color="#555555"),
        tickfont=dict(color="#666666")
    ),
    yaxis=dict(
        gridcolor="#e0e0e0",
        title_font=dict(size=14, color="#555555"),
        tickfont=dict(color="#666666")
    ),
    legend=dict(
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#cccccc",
        borderwidth=1,
        font=dict(color="#444444")
    )))

FILE_PATH = "STREAMLIT/CONTROLE-NOTAS/Notas.csv"
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


def show_pcm_page():
    """Mostra o conteúdo da página de DashBoard"""
    
    df_original = carregar_dados_csv()

    if df_original is None:
        st.error("Não foi possível carregar os dados.")
        st.stop()
    
    st.title("DASHBORDS 💹")
    df_sem_data = df_original[df_original['GESTORASSINATURA'].isnull() | (df_original['GESTORASSINATURA'] == '') | (df_original['GESTORASSINATURA'] == pd.NA)]
    

    with st.expander("Tabela de Dados"):
        tab1, tab2 = st.tabs(["SEM ASSINATURA", "GERAL"])

        with tab1:
            option = st.selectbox(
                "SELECIONE O GESTOR",
                ("GERAL","KATIA","DANILO", "HEBERTON","DANILO"))
            if option == 'GERAL':
                df_sem_data
            else:
                df_sem_data[df_sem_data['GESTOR_RESP']==option]

        with tab2:
            option1 = st.selectbox(
                "SELECIONE O GESTOR:",
                ("GERAL","KATIA","DANILO", "HEBERTON","DANILO"))
            if option1 == 'GERAL':
                df_original
            else:
                df_original[df_original['GESTOR_RESP']==option1]


    st.markdown("### Novo Gráficos à caminho  🛺")

    df_fig1 = df_sem_data.iloc[:,4].value_counts().reset_index()
    df_fig1.columns = ["Gestor","Qtd"]
    
    fig1 = px.bar(data_frame=df_fig1,x="Gestor",y='Qtd',title="Notas não assinadas",template=template_3
                ,color_discrete_sequence=["#0c162c"], text_auto=True)

    fig2 = px.pie(data_frame=df_fig1, values='Qtd',names="Gestor",color_discrete_sequence=["#0c162c","#5e7c7d","#94bfc8","#d9e0e2"],title="Notas não assinadas")

    pg1, pg2 = st.columns(2)

    pg1.plotly_chart(fig1)
    pg2.plotly_chart(fig2)  


show_pcm_page()


