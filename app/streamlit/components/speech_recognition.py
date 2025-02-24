import os
import azure.cognitiveservices.speech as speechsdk
import dotenv
import requests 
import spacy
import dateparser
from datetime import datetime


dotenv.load_dotenv(r"Vocal_Weather\var.env")

API_KEY = "b6cf1eceaa703e0b9f80b3f9453ff79a"
WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather'
WEATHER_URL_PREVISION = 'http://api.openweathermap.org/data/2.5/forecast'
GEOCODING_URL = 'http://api.openweathermap.org/geo/1.0/direct?'

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
            
            
recognize_from_microphone()


# Charger le modèle de langue française
nlp = spacy.load("fr_core_news_md")

#def extract_entities_ville(text):
    #doc = nlp(text)
    #city_name = None
    #horizon = None

    #for ent in doc.ents:
        #if ent.label_ == "LOC":  # Pour les lieux, y compris les villes
            #city_name = ent.text

    #return city_name

def horizon(text):
    """
    Extrait les dates d'un texte et les convertit en format standard (YYYY-MM-DD).
    Utilise dateparser pour gérer les dates relatives.
    """
    doc = nlp(text)
    dates_normalisées = []

    for ent in doc.ents:
        if ent.label_ == "DATE":
            date_str = ent.text.lower()

            # Utiliser dateparser pour reconnaître toutes les dates (relatives et absolues)
            date_obj = dateparser.parse(date_str, languages=["fr"])

            if date_obj:
                dates_normalisées.append(date_obj.strftime(f"%d-%m-%Y"))

    return dates_normalisées

#def get_coordinates(city_name):
    #params = {
        #'q': city_name,
        #'appid': API_KEY,
        #'limit': 1
    #}
    #response = requests.get(GEOCODING_URL, params=params)
    #data = response.json()
    #if data and len(data) > 0 and 'lat' in data[0] and 'lon' in data[0]:
        #return data[0]['lat'], data[0]['lon']
    #else:
        #return None, None

#def get_weather(lat, lon):
    #params = {
        #'lat': lat,
        #'lon': lon,
        #'appid': API_KEY,
        #'lang': 'fr',
        #'units': 'metric'
    #}
    #response = requests.get(WEATHER_URL, params=params)
    #return response.json()

#def get_weather_forecast(lat, lon):
    #params = {
        #'lat': lat,
        #'lon': lon,
        #'appid': API_KEY,
        #'units': 'metric'
    #}   
    #response = requests.get(WEATHER_URL_PREVISION, params=params)
    #return response.json()
