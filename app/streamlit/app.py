import multiprocessing
import os
import threading
import time
import pandas as pd
import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
import datetime



#---------------------- Definition des fonctions FastAPI ---------------------------------
#load_dotenv(r"Vocal_Weather\var.env")

# Lancer l'application FastAPI
# uvicorn app.main:app --reload



#---------------------------------- Fonction pour obtenir la reconnaissance ----------------------------------
def get_reconnaissance():
    res = requests.get("http://localhost:8000/reconnaissance", params={})
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur lors de la décodage de la réponse JSON. La réponse de l'API est vide ou mal formée.")
        return None

#---------------------------------- Fonction pour extraire les entités ----------------------------------
def extract_entities(text):
    res = requests.get("http://localhost:8000/extraction_entites", params={"text": text})
    return res.json()

#---------------------------------- Fonction pour extraire les entités ville ----------------------------------
def extract_entities_ville(text):
    res = requests.get("http://localhost:8000/extraction_entites_ville", params={"text": text})
    
    # Vérification de la validité de la réponse
    if res.status_code != 200:
        st.error(f"Erreur lors de la requête : {res.status_code}")
        return None
    
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur de décodage JSON : la réponse n'est pas valide ou est vide.")
        return None

# Fonction pour extraire les entités jours
def extract_entities_jours(text):
    res = requests.get("http://localhost:8000/extraction_entites_jours", params={"text": text})
    return res.json()

#---------------------------------- Fonction pour obtenir les prévisions météorologiques ----------------------------------
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
    
def get_daily_weather_forecast(city_name):
    res = requests.get("http://localhost:8000/meteo_prevision_journaliere", params={"city_name": city_name})
    if res.status_code != 200:
        st.error(f"Erreur lors de la requête : {res.status_code}")
        return None
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur de décodage JSON : la réponse n'est pas valide ou est vide.")
        return None

#---------------------- Interface Streamlit V1 ---------------------------------

st.title("Application de prévision météorologique (Open-Meteo)")
mode = st.radio("Sélectionnez le mode de commande :", ("Enregistrement par micro", "text", "Manuelle"))

transcription_input = ""
forecast_days_input = None
audio_bytes = None

if "forecast_response" not in st.session_state:
    st.session_state["forecast_response"] = None


if mode != "Enregistrement par micro":
    forecast_days_input = st.selectbox("Nombre de jours de prévision", options=[1,2,3,4,5,6,7], index=2)
else:
    forecast_days_input = 7

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
            meteo_data_journaliere = get_daily_weather_forecast(city_input)
            if meteo_data:
                st.session_state.forecast_response = meteo_data
                st.session_state.forecast_response_journaliere = meteo_data_journaliere
                st.success(f"Prévision pour {city_input}")
            else:
                st.error("Erreur lors de la récupération des données météorologiques.")
elif mode == "Manuelle":
    st.subheader("Commande manuelle")
    city_input = st.text_input("Ville")
    if st.button("Envoyer la commande"):
        meteo_data = get_weather_forecast(city_input)
        meteo_data_journaliere = get_daily_weather_forecast(city_input)
        if meteo_data:
            st.session_state.forecast_response = meteo_data
            st.session_state.forecast_response_journaliere = meteo_data_journaliere
            st.success(f"Prévision pour {city_input}")
else:
    text = st.text_area("Veuillez ecrire ce que vous souhaitez faire")
    ville = extract_entities_ville(text)
    jours = extract_entities_jours(text)
    st.write(f"Ville: {ville}")
    st.write(f"Jours: {jours}")
    if st.button("Envoyer la commande"):
        meteo_data = get_weather_forecast(ville)
        meteo_data_journaliere = get_daily_weather_forecast(ville)
        if meteo_data:
            st.session_state.forecast_response = meteo_data
            st.session_state.forecast_response_journaliere = meteo_data_journaliere
            st.success(f"Prévision pour {ville} pour {jours} jours")
        
#---------------------------------- Affichage des résultats (12 heures) ---------------------------------
if st.session_state.forecast_response:
    tab1, tab2, tab3, tab4 = st.tabs(["afficher les résultats sous forme de graphique", "afficher les résultats sous forme de tableau", "afficher les résultats sous forme de texte", "afficher les résultats par heure"])
    meteo_data = st.session_state.forecast_response
    # Convertir meteo_data en DataFrame
    df_meteo = pd.DataFrame(meteo_data)

    # Convertir la colonne 'date' en type datetime
    df_meteo['date'] = pd.to_datetime(df_meteo['date'])

    df_filtered = df_meteo[df_meteo['date'].dt.hour == 12].sort_values(by='date').head(forecast_days_input)
    
    with tab1:
        st.subheader("Prévisions de la journée")
        if st.session_state.forecast_response_journaliere and st.session_state.forecast_response:
            #---------------------------------- Prévisions de la journée ---------------------------------
            jour_selectionne = st.radio("Sélectionnez la journée si vous voulez afficher les prévisions de la journée:",options=["Données générales","Données détaillées"])
            # Assurez-vous que meteo_data est défini
            if jour_selectionne == "Données générales":
                meteo_data_journaliere = st.session_state.forecast_response_journaliere
                df_meteo_journaliere = pd.DataFrame(meteo_data_journaliere)
                df_meteo_journaliere['date'] = pd.to_datetime(df_meteo_journaliere['date'])
                
                # Obtenir toutes les dates disponibles
                available_dates = df_meteo_journaliere['date'].dt.strftime('%Y-%m-%d').unique()
                
                # Sélecteur de dates multiples
                selected_dates = st.multiselect("Sélectionnez les dates à afficher :", available_dates, default=available_dates)
                
                # Filtrer les données pour les dates sélectionnées
                df_selected = df_meteo_journaliere[df_meteo_journaliere['date'].dt.strftime('%Y-%m-%d').isin(selected_dates)]
                
                for index, row in df_selected.iterrows():
                    date = row['date'].strftime('%Y-%m-%d')
                    temperature_min = row['temperature_min']
                    temperature_max = row['temperature_max']
                    sunrise = datetime.datetime.strptime(row['sunrise'], '%Y-%m-%dT%H:%M').strftime('%H:%M')
                    sunset = datetime.datetime.strptime(row['sunset'], '%Y-%m-%dT%H:%M').strftime('%H:%M')
                    windspeed_max = row['windspeed_10m_max']
                    windspeed_min = row['windspeed_10m_min']
                    
                    # Utilisation d'icônes génériques
                    temperature_icon = "🌡️"
                    wind_icon = "💨"
                    sunrise_icon = "🌅"
                    sunset_icon = "🌇"

                    # Afficher les informations avec les icônes
                    st.write(f"**{date}**")
                    st.write(f" {temperature_icon}Température min: {temperature_min}°C,  {temperature_icon} Température max: {temperature_max}°C")
                    st.write(f" {wind_icon}Vent min: {windspeed_min} km/h, {wind_icon} Vent max: {windspeed_max} km/h ")
                    st.write(f" {sunrise_icon}Lever de soleil: {sunrise}, {sunset_icon} Coucher de soleil: {sunset}")
                    st.write("---")
            
            #---------------------------------- Prévision de la journée with hourly ---------------------------------
            if jour_selectionne == "Données détaillées":
                fig = make_subplots(rows=2, cols=2, shared_xaxes=True, vertical_spacing=0.08,
                                    subplot_titles=(f"Température (°C)", f"Précipitations (mm)", f"Nébulosité (%)", f"Vent (km/h)"))
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
        
        # Convertir meteo_data en DataFrame
        df_meteo = pd.DataFrame(meteo_data)
        df_meteo['date'] = pd.to_datetime(df_meteo['date'])
        
        # Filtrer les données pour ne garder que les enregistrements de midi
        df_filtered = df_meteo[df_meteo['date'].dt.hour == 12]
        
        # Afficher toutes les prévisions
        for index, row in df_filtered.iterrows():
            date = row['date'].strftime('%Y-%m-%d')
            temperature = row['temperature_2m']
            precipitation = row['precipitation']
            cloudcover = row['cloudcover']
            windspeed = row['windspeed_10m']
            pm2_5 = row['pm2_5']
            
            # Déterminer les icônes
            weather_icon = "☁️" if cloudcover > 75 else "🌥️" if cloudcover > 50 else "⛅" if cloudcover > 25 else "☀️"
            precipitation_icon = "🌧️" if precipitation > 20 else "🌦️" if precipitation > 5 else "🌂" if precipitation > 0 else "☂️"
            wind_icon = "💨" if windspeed > 50 else "🌬️" if windspeed > 20 else "🍃"
            pollution_icon = "🌫️" if pm2_5 > 50 else "🌫️" if pm2_5 > 20 else "🌳"
            temperature_icon = "🔥" if temperature > 30 else "🌞" if temperature > 20 else "🌤️"

            # Afficher les informations avec les icônes
            st.write(f"**{date}**")
            st.write(f"Température : {temperature}°C {temperature_icon}")
            st.write(f"Précipitations : {precipitation} mm {precipitation_icon}")
            st.write(f"Nébulosité : {cloudcover}% {weather_icon}")
            st.write(f"Vent : {windspeed} km/h {wind_icon}")
            st.write(f"Pollution : {pm2_5} µg/m³ {pollution_icon}")
            st.write("---")

        # Ajout d'un sélecteur de date
        dates = df_filtered['date'].dt.strftime('%Y-%m-%d').unique()
        selected_date = st.radio("Sélectionnez une date pour afficher les prévisions détaillées :", dates)

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
            
            # Afficher les informations détaillées avec les icônes
            st.write(f"**Détails pour {date}**")
            st.write(f"Température : {temperature}°C {temperature_icon}")
            st.write(f"Précipitations : {precipitation} mm {precipitation_icon}")
            st.write(f"Nébulosité : {cloudcover}% {weather_icon}")
            st.write(f"Vent : {windspeed} km/h {wind_icon}")
            st.write(f"Pollution : {pm2_5} µg/m³ {pollution_icon}")

#---------------------------------- Affichage des résultats (par heure) ---------------------------------
    with tab4:
        if st.session_state.forecast_response:
            # Assurez-vous que meteo_data est défini
            meteo_data = st.session_state.forecast_response

            # Convertir meteo_data en DataFrame
            df_meteo = pd.DataFrame(meteo_data)

            # Convertir la colonne 'date' en type datetime
            df_meteo['date'] = pd.to_datetime(df_meteo['date'])

            # Filtrer les données pour toutes les heures disponibles
            df_filtered = df_meteo.sort_values(by='date').head(forecast_days_input * 24)  # Supposant 24 heures par jour

            # Ajout d'un sélecteur d'heure
            available_hours = df_filtered['date'].dt.strftime('%Y-%m-%d %H:%M').unique()
            selected_hour = st.selectbox("Sélectionnez une heure pour afficher les prévisions :", available_hours)

            # Filtrer les données pour l'heure sélectionnée
            selected_data = df_filtered[df_filtered['date'].dt.strftime('%Y-%m-%d %H:%M') == selected_hour]

            # Afficher les informations pour l'heure sélectionnée
            if not selected_data.empty:
                row = selected_data.iloc[0]
                temperature = row['temperature_2m']
                precipitation = row['precipitation']
                cloudcover = row['cloudcover']
                windspeed = row['windspeed_10m']
                pm2_5 = row['pm2_5']

                st.write(f"**{selected_hour}**")
                st.write(f"Température : {temperature}°C {temperature_icon}")
                st.write(f"Précipitations : {precipitation} mm {precipitation_icon}")
                st.write(f"Nébulosité : {cloudcover}% {weather_icon}")
                st.write(f"Vent : {windspeed} km/h {wind_icon}")
                st.write(f"Pollution : {pm2_5} µg/m³ {pollution_icon}")

            fig = make_subplots(rows=2, cols=2, shared_xaxes=True, vertical_spacing=0.08,
                                subplot_titles=(f"Température (°C) {temperature_icon}", f"Précipitations (mm) {precipitation_icon}", f"Nébulosité (%) {weather_icon}", f"Vent (km/h) {wind_icon}"))
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['temperature_2m'],
                                     mode='lines+markers', marker=dict(color='red')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['precipitation'],
                                     mode='lines+markers', marker=dict(color='blue')), row=1, col=2)
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['cloudcover'],
                                     mode='lines+markers', marker=dict(color='blue')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['windspeed_10m'],
                                     mode='lines+markers', marker=dict(color='green')), row=2, col=2)
            fig.update_layout(height=800, title=f"Prévisions horaires sur {forecast_days_input} jours", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
