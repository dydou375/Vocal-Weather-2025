import pandas as pd
import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv

def monitoring():
    res = requests.get("http://localhost:8000/monitoring", params={})
    return res.json()


st.header("Analyse et Monitoring")
try:
    response = monitoring()
    if response:
        st.write("Logs de requêtes :")
        df_logs = pd.DataFrame(response, columns=["Timestamp", "Method", "Endpoint", "HTTP Status"])
        st.dataframe(df_logs)

        # Graphique du nombre de requêtes par heure
        df_logs['Timestamp'] = pd.to_datetime(df_logs['Timestamp'])
        df_logs['Hour'] = df_logs['Timestamp'].dt.hour
        requests_per_hour = df_logs.groupby('Hour').size().reset_index(name='Request Count')

        fig = go.Figure(data=go.Bar(x=requests_per_hour['Hour'], y=requests_per_hour['Request Count']))
        fig.update_layout(title="Nombre de requêtes par heure", xaxis_title="Heure", yaxis_title="Nombre de requêtes")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Erreur lors de la récupération des données de monitoring.")
except Exception as e:
    st.error("Impossible de joindre le backend pour l'analyse.")