import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv
import spacy
import dateparser
#from speech_recognition import recognize_from_microphone

#---------------------- Definition des fonctions FastAPI ---------------------------------
#load_dotenv(r"Vocal_Weather\var.env")
"""def get_reconnaissance():
    res = requests.get("http://localhost:8000/reconnaissance", params={})
    return res.json()"""

"""def get_horizon(city_name):
    res = requests.get("http://localhost:8000/horizon_date", params={"city_name": city_name})
    return res.json()"""
    
def extract_entities_ville(text):
    res = requests.get("http://localhost:8000/ville", params={"text": text})
    return res.json()

def get_coordinates_V1(city_name):
    res = requests.get("http://localhost:8000/ville_coordonnees_V1", params={"city_name": city_name})
    return res.json()


def get_coordinates_V2(city_name):
    res = requests.get("http://localhost:8000/ville_coordonnees_V2", params={"city_name": city_name})
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Erreur lors de la récupération des coordonnées. La réponse de l'API est vide ou mal formée.")
        return None
    
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


#---------------------- Interface Streamlit ---------------------------------

st.title("Application Météo avec Open Météo")

# Utiliser la reconnaissance vocale pour obtenir la commande
bouton_vocal = st.text_input("VEUILLEZ ENTREZ LE NOM DE LA VILLE")
if bouton_vocal:
    city_name = extract_entities_ville(bouton_vocal)
    st.write(f"Ville: {city_name}")
    
    if not city_name:
        st.error("Ville non reconnue dans la commande.")
    else:
        weather_data = get_meteo_prevision(city_name)
        st.dataframe(weather_data)
        

