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

def get_coordinates():
    res = requests.get("http://localhost:8000/coordinates", params={})
    return res.json()

def get_ville(text):
    res = requests.get("http://localhost:8000/ville", params={"text": text})
    return res.json()

def get_horizon(text):
    res = requests.get("http://localhost:8000/horizon", params={"text": text})
    return res.json()   

def get_meteo():
    res = requests.get("http://localhost:8000/meteo", params={})
    return res.json()

def get_meteo_prevision():
    res = requests.get("http://localhost:8000/meteo_prevision", params={})
    return res.json()   


#---------------------- Interface Streamlit ---------------------------------

st.title("Application Météo avec OpenWeatherMap")

# Utiliser la reconnaissance vocale pour obtenir la commande
bouton_vocal = st.text_area("meteo")

if bouton_vocal:
    city_name = get_ville(bouton_vocal)
    horizon = get_horizon(bouton_vocal)
    
    st.write(f"Ville: {city_name}")
    st.write(f"Horizon: {horizon}")
    
    if not city_name:
        st.error("Ville non reconnue dans la commande.")
    else:
        lat, lon = get_coordinates(city_name)
        
        
        if lat is None or lon is None:
            st.error("Ville non trouvée ou erreur dans la requête.")
        else:
            weather_data = get_meteo(lat, lon)
            
            if weather_data.get('cod') != 200:
                st.error("Erreur dans la récupération des données météorologiques.")
            else:
                temperature = weather_data['main']['temp']
                description = weather_data['weather'][0]['description']
                st.write(f"La température actuelle à {city_name} est de {temperature}°C avec {description}.")

                
                if horizon:
                    weather_data_forecast = get_meteo_prevision(lat, lon)
                    st.write(f"Prévision pour : {horizon}")
                    st.write(f"Prévision pour : {weather_data_forecast}")

