import pandas as pd
import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv

#---------------------- Definition des fonctions FastAPI ---------------------------------
#load_dotenv(r"Vocal_Weather\var.env")

# Fonction pour obtenir la reconnaissance
def get_reconnaissance():
    res = requests.get("http://localhost:8000/reconnaissance", params={})
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur lors de la décodage de la réponse JSON. La réponse de l'API est vide ou mal formée.")
        return None

# Fonction pour extraire les entités
def extract_entities(text):
    res = requests.get("http://localhost:8000/extraction_entites", params={"text": text})
    return res.json()

# # Fonction pour extraire les entités ville
# def extract_entities_ville(text):
#     res = requests.get("http://localhost:8000/extraction_entites_ville", params={"text": text})
    
#     # Vérification de la validité de la réponse
#     if res.status_code != 200:
#         st.error(f"Erreur lors de la requête : {res.status_code}")
#         return None
    
#     try:
#         return res.json()
#     except requests.exceptions.JSONDecodeError:
#         st.error("Erreur de décodage JSON : la réponse n'est pas valide ou est vide.")
#         return None

# # Fonction pour extraire les entités jours
# def extract_entities_jours(text):
#     res = requests.get("http://localhost:8000/extraction_entites_jours", params={"text": text})
#     return res.json()

# Fonction pour obtenir les prévisions météorologiques
def get_weather_forecast(city_name):
    res = requests.get("http://localhost:8000/meteo_prevision", params={"city_name": city_name})
    
    # Vérification de la validité de la réponse
    if res.status_code != 200:
        st.error(f"Erreur lors de la requête : {res.status_code}")
        return None
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur de décodage JSON : la réponse n'est pas valide ou est vide.")
        return None
    
# Fonction pour obtenir les données de monitoring
def get_monitoring():
    res = requests.get("http://localhost:8000/monitoring", params={})
    return res.json()  




#---------------------- Interface Streamlit V1 ---------------------------------

st.title("Application de prévision météorologique (Open-Meteo)")
mode = st.radio("Sélectionnez le mode de commande :", ("Enregistrement par micro", "Manuelle"))
transcription_input = ""
forecast_days_input = None
audio_bytes = None

if "forecast_response" not in st.session_state:
    st.session_state["forecast_response"] = None


if mode != "Enregistrement par micro":
    forecast_days_input = st.selectbox("Nombre de jours de prévision", options=[3, 5, 7], index=2)
    
if mode == "Enregistrement par micro":
    st.subheader("Commande vocale via microphone")
    if st.button("Enregistrer la commande vocale"):
        st.info("Veuillez parler maintenant...")
        command_vocal = get_reconnaissance()
        if command_vocal == None:
            st.error("Aucune commande reconnue.")
        else:
            st.session_state.micro_transcription = command_vocal
    if "micro_transcription" in st.session_state and st.session_state.micro_transcription:
        st.write("Transcription obtenue :", st.session_state.micro_transcription)
        city_input = extract_entities(st.session_state.micro_transcription)
        if st.button("Envoyer la commande vocale"):
            meteo_data = get_weather_forecast(city_input)
            if meteo_data:
                st.session_state.forecast_response = meteo_data
                st.success(f"Prévision pour {city_input}")
            else:
                st.error("Erreur lors de la récupération des données météorologiques.")
else:
    st.subheader("Commande manuelle")
    city_input = st.text_input("Ville")
    if st.button("Envoyer la commande"):
        meteo_data = get_weather_forecast(city_input)
        if meteo_data:
            st.session_state.forecast_response = meteo_data
            st.success(f"Prévision pour {city_input}")

if st.session_state.forecast_response and st.button("Afficher les résultats"):
    # Assurez-vous que meteo_data est défini
    meteo_data = st.session_state.forecast_response
    
    # Convertir meteo_data en DataFrame
    df_meteo = pd.DataFrame(meteo_data)
    
    # Convertir la colonne 'date' en type datetime
    df_meteo['date'] = pd.to_datetime(df_meteo['date'])
    
    df_filtered = df_meteo[df_meteo['date'].dt.hour == 12].sort_values(by='date').head(forecast_days_input)
        
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("Température (°C)", "Nébulosité (%)", "Vent (km/h)"))
    fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['temperature_2m'],
                                mode='lines+markers', marker=dict(color='red')), row=1, col=1)
    # fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['rain'],
    #                         mode='lines+markers', marker=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['cloudcover'],
                            mode='lines+markers', marker=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['windspeed_10m'],
                            mode='lines+markers', marker=dict(color='green')), row=3, col=1)
    fig.update_layout(height=600, title=f"Prévisions de Midi sur {forecast_days_input} jours", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
        
    st.subheader("Détails des prévisions")
    st.dataframe(df_filtered[['date', 'temperature_2m', 'cloudcover', 'windspeed_10m', 'pm2_5']].rename(
            columns={
                "date": "Date",
                "temperature_2m": "Température (°C)",
                "cloudcover": "Nébulosité (%)",
                "windspeed_10m": "Vent (km/h)",
                "pm2_5": "Pollution (µg/m³)"
            }
        ))

