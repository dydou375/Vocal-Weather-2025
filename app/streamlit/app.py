import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv
import spacy
import dateparser
#from speech_recognition import recognize_from_microphone

#---------------------- Definition des fonctions FastAPI ---------------------------------
#load_dotenv(r"Vocal_Weather\var.env")
def get_reconnaissance():
    res = requests.get("http://localhost:8000/reconnaissance", params={})
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur lors de la décodage de la réponse JSON. La réponse de l'API est vide ou mal formée.")
        return None

"""def get_horizon(text):
    res = requests.get("http://localhost:8000/periode", params={"text": text})
    return res.json()"""
    
def extract_entities_ville(text):
    res = requests.get("http://localhost:8000/ville", params={"text": text})
    return res.json()
    
def get_meteo_prevision(city_name):
    res = requests.get("http://localhost:8000/meteo_prevision", params={"city_name": city_name})
    
    # Vérifier si la requête a réussi
    if res.status_code == 200:
        try:
            return res.json()
        except requests.exceptions.JSONDecodeError:
            st.error("Erreur lors de la décodage de la réponse JSON. La réponse de l'API est vide ou mal formée.")
            return None
    else:
        st.error(f"Erreur lors de la récupération des données météorologiques. Code d'erreur: {res.status_code}")
        return None

def get_monitoring():
    res = requests.get("http://localhost:8000/monitoring", params={})
    return res.json()  

def get_weather_forecast_seb(city_name):
    res = requests.get("http://localhost:8000/meteo_prevision_seb", params={"city_name": city_name})
    
    # Vérification de la validité de la réponse
    if res.status_code != 200:
        st.error(f"Erreur lors de la requête : {res.status_code}")
        return None
    
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur de décodage JSON : la réponse n'est pas valide ou est vide.")
        return None


#---------------------- Interface Streamlit ---------------------------------

st.title("Application Météo avec Open Météo")

# Utiliser la reconnaissance vocale pour obtenir la commande
commande = st.button("Reconnaissance")

if commande:
    command_vocal = get_reconnaissance()
    if command_vocal == None:
        st.error("Aucune commande reconnue.")
    else:
        st.write(f"Commande: {command_vocal}")
        city_name = extract_entities_ville(command_vocal)
        st.write(f"Ville: {city_name}")
        if not city_name:
            st.error("Ville non reconnue dans la commande.")
        else:
            weather_data = get_meteo_prevision(city_name)
            st.dataframe(weather_data)
            weather_data_seb = get_weather_forecast_seb(city_name)
            st.dataframe(weather_data_seb)

