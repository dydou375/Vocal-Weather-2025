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
import streamlit as st

# Configuration du client Open-Meteo API avec cache et retry en cas d'erreur
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


dotenv.load_dotenv(r"Vocal_Weather\var.env")
SPEECH_KEY = "54124b94ae904eeea1d8a652a4c3d88d"
SPEECH_REGION = "francecentral"


def recognize_from_microphone():
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_recognition_language="fr-FR"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    st.write("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))
        return speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
        return None

def extract_entities_ville(text):
    nlp = spacy.load("fr_core_news_md")
    doc = nlp(text)
    city_name = None
    horizon = None

    for ent in doc.ents:
        if ent.label_ == "LOC":  # Pour les lieux, y compris les villes
            city_name = ent.text

    return city_name

def get_coordinates_V1(city_name):
    API_KEY = "b6cf1eceaa703e0b9f80b3f9453ff79a"
    GEOCODING_URL = 'http://api.openweathermap.org/geo/1.0/direct?'
    params = {
        'q': city_name,
        'appid': API_KEY,
        'limit': 1
    }
    response = requests.get(GEOCODING_URL, params=params)
    data = response.json()
    if data and len(data) > 0 and 'lat' in data[0] and 'lon' in data[0]:
        return data[0]['lat'], data[0]['lon']
    else:
        return None, None
    
    
def get_coordinates_V2(city_name) -> Tuple[float, float]:
    geocode_url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json"}
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(geocode_url, params=params, headers=headers)
    data = r.json()
    print(data)
    if not data:
        raise Exception(f"Ville introuvable : {city_name}")
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return lat, lon


def get_weather_forecast(city_name):
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    if city_name == "":
        return None
    else:
        lat, lon = get_coordinates_V2(city_name)

    if lat is None or lon is None:
        return None
    else:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,rain,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,is_day",
            "timezone": "Europe/Paris",
            "timezone_abbreviation": "CET"
        }

    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_rain = hourly.Variables(1).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(2).ValuesAsNumpy()
    hourly_cloud_cover_low = hourly.Variables(3).ValuesAsNumpy()
    hourly_cloud_cover_mid = hourly.Variables(4).ValuesAsNumpy()
    hourly_cloud_cover_high = hourly.Variables(5).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(6).ValuesAsNumpy()
    hourly_is_day = hourly.Variables(7).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m.tolist()
    hourly_data["rain"] = hourly_rain.tolist()
    hourly_data["cloud_cover"] = hourly_cloud_cover.tolist()
    hourly_data["cloud_cover_low"] = hourly_cloud_cover_low.tolist()
    hourly_data["cloud_cover_mid"] = hourly_cloud_cover_mid.tolist()
    hourly_data["cloud_cover_high"] = hourly_cloud_cover_high.tolist()
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m.tolist()
    hourly_data["is_day"] = hourly_is_day.tolist()

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    return hourly_dataframe

def get_weather_forecast_seb(city_name: str) -> pd.DataFrame:
    lat, lon = get_coordinates_V2(city_name)
    url = "https://api.open-meteo.com/v1/forecast"
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
