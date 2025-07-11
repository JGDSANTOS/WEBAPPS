#Bibliotecas
import pandas as pd
import datetime as dt

#Arquivo
df = pd.read_excel(r"STREAMLIT/DB_LOGISTICAL/PYTHON/BD_Logistica.xlsx")

df[['Cliente', 'Motorista']] = df['Cliente - Motorista'].str.split('-', expand=True)
df.drop('Cliente - Motorista', axis=1, inplace=True)

df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x )


#Aplicando o formato correto nas colunas de data
colunas_datas = [
    'Data Entrega Real',
    'Data Emissão Pedido',
    'Data Entrega Prevista',
    'Saída para Entrega'
]

for coluna in colunas_datas:
    df[coluna] = pd.to_datetime(df[coluna], errors='coerce', dayfirst=True)

import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide", page_title= "DASHBOARD LOGISTICA",initial_sidebar_state="expanded")

#st.write(' # :orange[Dashboard Logística]')
st.write(' # Dashboard Logística')
#st.html("<title>Dashboard Logística</title>")
#st.markdown('**Dashboard Logística**')


with st.expander("Veja a tabela"):
    st.dataframe(df)

col1, col2, col3, col4, col5, col12 = st.columns(6)
col6, col7, col8 = st.columns(3)
col9, col10, col11 = st.columns(3)


#Column 1
Pedidos = df['Nº Pedido'].count()
col1.metric("Pedidos",Pedidos)

#Column 2
Itens = df['Itens'].sum()
col2.metric("Itens",Itens)


#Column 3 
Itens_Devolucao = df[' Qtd Devolução'].sum()
col3.metric("Itens Devolução",Itens_Devolucao)


#Column 4
Faturamento = df['R$ Faturados'].sum()
Faturamento = Faturamento.round(2)
col4.metric("R$ Faturados",Faturamento)

#Column 5
Entregas_Atrasadas = (df.loc[df["Status"] == "Atrasado","Status"].count())/Pedidos*100
Entregas_Atrasadas = Entregas_Atrasadas.round(2)
col5.metric("% Entregas Atrasadas",Entregas_Atrasadas)


#Column 12
Devolucao_Itens = Itens_Devolucao/Itens*100
Devolucao_Itens = Devolucao_Itens.round(2)
col12.metric("%  Devolução de Itens", Devolucao_Itens)


#Column 6 
df_pedidos = df.groupby("Status")["Nº Pedido"].count().reset_index()
df_bar_status = px.bar(df_pedidos, x="Status",y="Nº Pedido", color="Status", title="Nº de Pedidos por Status",text_auto=True, color_discrete_sequence = ['#ff2e00', '#ff5010'])
col6.plotly_chart(df_bar_status)

#Column 7
df_prazo = df.groupby("Status")[" Qtd Devolução"].sum().reset_index()
df_prazo = df_prazo.pivot_table(columns="Status")
df_prazo_total = (df_prazo["Atrasado"]+df_prazo['No Prazo'])

df_prazo['Atrasado'] = (df_prazo["Atrasado"]/df_prazo_total * 100)
df_prazo['No Prazo'] = (df_prazo["No Prazo"]/df_prazo_total * 100)
df_prazo = df_prazo.round(2)

df_bar_prazo = px.bar(df_prazo, x=['Atrasado', 'No Prazo'], orientation='h',text_auto=True, title="% Itens Devolução por Status", color_discrete_sequence = ['#ff2e00', '#ff5010'])

col7.plotly_chart(df_bar_prazo)

#Column 8
df['Dias Previstos'] =  (df['Data Entrega Prevista'] - df["Data Emissão Pedido"])
df['Dias Reais'] = df['Data Entrega Real'] - df["Data Emissão Pedido"] 

df_dias = df.groupby("Destino")[["Dias Previstos", 'Dias Reais']].median().reset_index()
df_dias["Dias Previstos"] = df_dias["Dias Previstos"].astype(str).str.replace(" days","").astype(int)
df_dias["Dias Reais"] = df_dias["Dias Reais"].astype(str).str.replace(" days","").astype(int)

df_bar_dias = px.bar(df_dias, x = ["Dias Previstos", "Dias Reais"], y= "Destino", orientation="h",barmode='group',text_auto=True ,title="Lead Time Previsto x Real", color_discrete_sequence = ['#ff2e00', '#ff5010'])
col8.plotly_chart(df_bar_dias)

#Column 9
df_clientes = df.groupby(["Cliente","Status"])[["Nº Pedido"]].count().reset_index()
df_bar_clientes = px.bar(df_clientes, y = "Cliente", x="Nº Pedido", color="Status",text_auto=True , title= "Nº de Pedidos por Cliente e Status", orientation='h', color_discrete_sequence = ['#ff2e00', '#ff5010'])
col9.plotly_chart(df_bar_clientes)

#Column 10
df_motivo = df.groupby("Mot. Devolução")[" Qtd Devolução"].sum().reset_index()
df_motivo = df_motivo[df_motivo[" Qtd Devolução"]>0]
df_bar_motivo = px.bar(df_motivo, x = "Mot. Devolução", y = " Qtd Devolução",text_auto=True , title= "Quantidade de Devoluções por Motivo",  color_discrete_sequence = ['#ff2e00'])
col10.plotly_chart(df_bar_motivo)

#Column 11
df_motorista = df.groupby(["Motorista","Status"])[["Nº Pedido"]].count().reset_index()
df_bar_motorista = px.bar(df_motorista, x="Nº Pedido", y="Motorista",orientation='h',color="Status",barmode='group',text_auto=True,title="Nº de Pedidos por Motorista e Status", color_discrete_sequence = ['#ff2e00', '#ff5010'])
col11.plotly_chart(df_bar_motorista)
