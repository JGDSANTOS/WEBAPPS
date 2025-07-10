# app.py
import streamlit as st


st.set_page_config(page_title="App de Controle", layout="wide", initial_sidebar_state="auto")
sidebar_logo = "Logo_GYN_2.png"
main_logo = "Logo_GYN_1.png"
st.logo(sidebar_logo,icon_image=main_logo,size="large")


login_page = st.Page("Page_Assinatura.py", title="ASSINATURAS", icon="🔐")
pcm_page = st.Page("Page_Admin.py", title="CONTROLE DE NOTAS", icon="📝")
dash_page = st.Page("Page_DashBoards.py", title="DASHBOARDS", icon="📈")
test = st.Page("Page_Main.py", title="INICIO", icon="✨")


pg = st.navigation([test,login_page, dash_page, pcm_page])

pg.run()