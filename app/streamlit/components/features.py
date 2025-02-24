import os
import azure.cognitiveservices.speech as speechsdk
import dotenv
import requests 
import spacy
import dateparser
from datetime import datetime
from date_spacy import find_dates
from typing import Tuple

import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

# Configuration du client Open-Meteo API avec cache et retry en cas d'erreur
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


dotenv.load_dotenv(r"Vocal_Weather\var.env")


def recognize_from_microphone():
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
    speech_config.speech_recognition_language="fr-FR"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")


# Charger le modèle de langue française
#nlp = spacy.load("fr_core_news_md")

def extract_entities_ville(text):
    nlp = spacy.load("fr_core_news_md")
    doc = nlp(text)
    city_name = None
    horizon = None

    for ent in doc.ents:
        if ent.label_ == "LOC":  # Pour les lieux, y compris les villes
            city_name = ent.text

    return city_name

nlp_fr = spacy.blank('fr')
nlp_fr.add_pipe('find_dates')

def extract_dates(text):
    nlp_fr = spacy.blank('fr')
    nlp_fr.add_pipe('find_dates')
    doc = nlp_fr(text)
    dates = []
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            dates.append((ent.text, ent._.date))
    return dates

def horizon(text):
    """
    Extrait les dates d'un texte et les convertit en format standard (YYYY-MM-DD).
    Utilise dateparser pour gérer les dates relatives.
    """
    doc_dates = extract_dates(text)
    dates_normalisées = []

    for ent in doc_dates:
        if ent.label_ == "DATE":
            date_str = ent.text.lower()

            # Utiliser dateparser pour reconnaître toutes les dates (relatives et absolues)
            date_obj = dateparser.parse(date_str, languages=["fr"])

            if date_obj:
                dates_normalisées.append(date_obj.strftime(f"%d-%m-%Y"))

    return dates_normalisées

def get_coordinates(city_name) -> Tuple[float, float]:
    geocode_url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json"}
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(geocode_url, params=params, headers=headers)
    data = r.json()
    if not data:
        raise Exception(f"Ville introuvable : {city_name}")
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return lat, lon

def get_weather_forecast(city_name: str) -> pd.DataFrame:
    url = "https://api.open-meteo.com/v1/forecast"
    try:
        lat, lon = get_coordinates(city_name)
        print(lat, lon)
    except Exception as e:
        print(f"Erreur lors de la récupération des coordonnées de la ville {city_name}: {e}")
        return pd.DataFrame()
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,cloudcover,windspeed_10m",
        "timezone": "auto"
    }
    response = retry_session.get(url, params=params)
    data = response.json()
    times = pd.to_datetime(data['hourly']['time'])
    df = pd.DataFrame({
        "date": times,
        "temperature_2m": data['hourly']['temperature_2m'],
        "cloudcover": data['hourly']['cloudcover'],
        "windspeed_10m": data['hourly']['windspeed_10m'],
        "pm2_5": [12.3] * len(times)
    })
    return df


def monitoring():
    return "Monitoring"
