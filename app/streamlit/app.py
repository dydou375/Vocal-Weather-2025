import threading
import time
import pandas as pd
import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
import uvicorn
import subprocess



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
            
if st.session_state.forecast_response:
    tab1, tab2, tab3 = st.tabs(["afficher les résultats sous forme de graphique", "afficher les résultats sous forme de tableau", "afficher les résultats sous forme de texte"])

    with tab1:
        if st.session_state.forecast_response:
            # Assurez-vous que meteo_data est défini
            meteo_data = st.session_state.forecast_response

            # Convertir meteo_data en DataFrame
            df_meteo = pd.DataFrame(meteo_data)

            # Convertir la colonne 'date' en type datetime
            df_meteo['date'] = pd.to_datetime(df_meteo['date'])

            df_filtered = df_meteo[df_meteo['date'].dt.hour == 12].sort_values(by='date').head(forecast_days_input)

            fig = make_subplots(rows=2, cols=2, shared_xaxes=True, vertical_spacing=0.08,
                                subplot_titles=("Température (°C)", "Précipitations (mm)", "Nébulosité (%)", "Vent (km/h)"))
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['temperature_2m'],
                                     mode='lines+markers', marker=dict(color='red')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['precipitation'],
                                     mode='lines+markers', marker=dict(color='blue')), row=1, col=2)
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['cloudcover'],
                                     mode='lines+markers', marker=dict(color='blue')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['windspeed_10m'],
                                     mode='lines+markers', marker=dict(color='green')), row=2, col=2)
            fig.update_layout(height=600, title=f"Prévisions de Midi sur {forecast_days_input} jours", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Détails des prévisions")
        st.dataframe(df_filtered[['date', 'temperature_2m', 'precipitation', 'cloudcover', 'windspeed_10m', 'pm2_5']].rename(
            columns={
                "date": "Date",
                "temperature_2m": "Température (°C)",
                "precipitation": "Précipitations (mm)",
                "cloudcover": "Nébulosité (%)",
                "windspeed_10m": "Vent (km/h)",
                "pm2_5": "Pollution (µg/m³)"
            }
        ))

    with tab3:
        st.subheader("Détails des prévisions")
        
        # Assurez-vous que meteo_data est défini
        meteo_data = st.session_state.forecast_response
        
        # Ajout d'un sélecteur de date
        dates = df_filtered['date'].dt.strftime('%Y-%m-%d').unique()
        selected_date = st.radio("Sélectionnez une date pour afficher les prévisions :", dates)

        # Filtrer les données pour la date sélectionnée
        selected_data = df_filtered[df_filtered['date'].dt.strftime('%Y-%m-%d') == selected_date]

        # Afficher les informations pour la date sélectionnée
        if not selected_data.empty:
            row = selected_data.iloc[0]
            date = row['date'].strftime('%Y-%m-%d')
            temperature = row['temperature_2m']
            precipitation = row['precipitation']
            cloudcover = row['cloudcover']
            windspeed = row['windspeed_10m']
            pm2_5 = row['pm2_5']
            
            # Déterminer l'icône en fonction de la nébulosité
            if cloudcover > 75:
                weather_icon = "☁️"  # Très nuageux
            elif cloudcover > 50:
                weather_icon = "🌥️"  # Partiellement nuageux
            elif cloudcover > 25:
                weather_icon = "⛅"  # Peu nuageux
            else:
                weather_icon = "☀️"  # Ensoleillé

            # Déterminer l'icône en fonction des précipitations
            if precipitation > 20:
                precipitation_icon = "🌧️"  # Pluie forte
            elif precipitation > 5:
                precipitation_icon = "🌦️"  # Pluie modérée
            elif precipitation > 0:
                precipitation_icon = "🌂"  # Pluie légère
            else:
                precipitation_icon = "☂️"  # Pas de pluie

            # Déterminer l'icône en fonction de la vitesse du vent
            if windspeed > 50:
                wind_icon = "💨"  # Vent fort
            elif windspeed > 20:
                wind_icon = "🌬️"  # Vent modéré
            else:
                wind_icon = "🍃"  # Vent léger
                
            # Déterminer l'icône en fonction de la pollution
            if pm2_5 > 50:
                pollution_icon = "🌫️"  # Pollution forte
            elif pm2_5 > 20:
                pollution_icon = "🌫️"  # Pollution modérée
            else:
                pollution_icon = "🌳"  # Pollution légère
                
            # Déterminer l'icône en fonction de la température
            if temperature > 30:
                temperature_icon = "🔥"  # Température élevée
            elif temperature > 20:
                temperature_icon = "🌞"  # Température modérée
            else:
                temperature_icon = "🌤️"  # Température basse

            # Afficher les informations avec les icônes
            st.write(f"**{date}**")
            st.write(f"Température : {temperature}°C {temperature_icon}")
            st.write(f"Précipitations : {precipitation} mm  {precipitation_icon}")
            st.write(f"Nébulosité : {cloudcover}% {weather_icon}")
            st.write(f"Vent : {windspeed} km/h  {wind_icon}")
            st.write(f"Pollution : {pm2_5} µg/m³ {pollution_icon}")
