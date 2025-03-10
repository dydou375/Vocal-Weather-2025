import os
import json
import datetime
import logging
import azure.cognitiveservices.speech as speechsdk
import dotenv
import requests
import spacy
import pandas as pd
import re
import uvicorn
import threading
import time
import tempfile
from functools import wraps
from typing import Tuple, Callable

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response, Request
from pydantic import BaseModel

import streamlit as st
import requests_cache
from retry_requests import retry

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import openmeteo_requests

dotenv.load_dotenv()

# Configuration PostgreSQL (Azure)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")


#Configuration du logging
logging.basicConfig(level=logging.INFO)
nlp = spacy.load("fr_core_news_md")
logs = []

#Configuration du client Open-Meteo API avec cache et retry en cas d'erreur
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

SPEECH_KEY = "54124b94ae904eeea1d8a652a4c3d88d"
SPEECH_REGION = "francecentral"

#---------------------------------- Reconnaissance vocale ----------------------------------
def recognize_from_microphone():
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_recognition_language="fr-FR"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    st.info("Veuillez parler... (attendez la fin de l'enregistrement)")
    retry_attempts = 3
    for attempt in range(retry_attempts):
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
        else:
            print(f"Erreur de reconnaissance vocale: {speech_recognition_result.reason}")
            return None

def extract_entities_ville(text):
    doc = nlp(text)
    location = None
    for ent in doc.ents:
        if ent.label_ in ["LOC", "GPE"] and not location:
            location = ent.text
    if not location:
        location = "Paris"
    return location

#---------------------------------- Extraction des entités ----------------------------------
def extract_forecast_days(text: str) -> int:
    regex_match = re.search(r"sur\s+(\d+)\s+jours", text, re.IGNORECASE)
    if regex_match:
        try:
            num = int(regex_match.group(1))
            if num in [3, 5, 7]:
                return num
        except Exception as e:
            logging.error(f"Erreur extraction jours: {e}")
    
    doc = nlp(text)
    for token in doc:
        if token.like_num:
            try:
                num = int(token.text)
                if num in [1, 2, 3, 4, 5, 6, 7]:
                    return num
            except Exception:
                continue
    
    return 7  # Valeur par défaut

def spacy_analyze(text: str) -> Tuple[str, int]:
    doc = nlp(text)
    location = None
    forecast_days = None
    regex_match = re.search(r"sur\s+(\d+)\s+jours", text, re.IGNORECASE)
    if regex_match:
        try:
            num = int(regex_match.group(1))
            if num in [3, 5, 7]:
                forecast_days = num
        except Exception as e:
            logging.error(f"Erreur extraction jours: {e}")
    if not forecast_days:
        for token in doc:
            if token.like_num:
                try:
                    num = int(token.text)
                    if num in [1,2,3,4,5,6,7]:
                        forecast_days = num
                        break
                except Exception:
                    continue
    for ent in doc.ents:
        if ent.label_ in ["LOC", "GPE"] and not location:
            location = ent.text
    if not location:
        location = "Paris"
    if not forecast_days:
        forecast_days = 7
    return location, forecast_days
    
#---------------------------------- Coordonnées des villes ----------------------------------
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

#---------------------------------- Prévision météorologique ----------------------------------
def get_weather_forecast(city_name: str) -> pd.DataFrame:
    lat, lon = get_coordinates_V2(city_name)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,rain,precipitation,cloudcover,windspeed_10m",
        "timezone": "auto"
    }
    response = retry_session.get(url, params=params)
    data = response.json()
    
    # Vérification des données reçues
    if 'hourly' not in data or not all(key in data['hourly'] for key in ['time', 'temperature_2m', 'precipitation', 'cloudcover', 'windspeed_10m']):
        raise ValueError("Données manquantes dans la réponse de l'API")
    
    times = pd.to_datetime(data['hourly']['time'])
    df = pd.DataFrame({
        "date": times,
        "temperature_2m": data['hourly']['temperature_2m'],
        "rain": data['hourly']['rain'],
        "precipitation": data['hourly']['precipitation'],
        "cloudcover": data['hourly']['cloudcover'],
        "windspeed_10m": data['hourly']['windspeed_10m'],
        "pm2_5": [12.3] * len(times)
    })
    # Convertir les types de données en types natifs Python
    df = df.astype({
        "temperature_2m": float,
        "rain": float,
        "precipitation": float,
        "cloudcover": float,
        "windspeed_10m": float
    })
    return df

def get_hourly_weather_forecast(city_name: str) -> pd.DataFrame:
    lat, lon = get_coordinates_V2(city_name)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,rain,precipitation,cloudcover,windspeed_10m",
        "timezone": "auto"
    }
    response = retry_session.get(url, params=params)
    data = response.json()
    
    # Vérification des données reçues
    if 'hourly' not in data or not all(key in data['hourly'] for key in ['time', 'temperature_2m', 'precipitation', 'cloudcover', 'windspeed_10m']):
        raise ValueError("Données manquantes dans la réponse de l'API")
    
    times = pd.to_datetime(data['hourly']['time'])
    df_hourly = pd.DataFrame({
        "date": times,
        "temperature_2m": data['hourly']['temperature_2m'],
        "rain": data['hourly']['rain'],
        "precipitation": data['hourly']['precipitation'],
        "cloudcover": data['hourly']['cloudcover'],
        "windspeed_10m": data['hourly']['windspeed_10m'],
        "pm2_5": [12.3] * len(times)
    })
    # Convertir les types de données en types natifs Python
    df_hourly = df_hourly.astype({
        "temperature_2m": float,
        "rain": float,
        "precipitation": float,
        "cloudcover": float,
        "windspeed_10m": float
    })
    
    return df_hourly

def get_daily_weather_forecast(city_name: str) -> pd.DataFrame:
    lat, lon = get_coordinates_V2(city_name)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_min,temperature_2m_max,sunrise,sunset,windspeed_10m_max,windspeed_10m_min",
        "timezone": "auto"
    }
    response = retry_session.get(url, params=params)
    data = response.json()
    
    # Traitement des données quotidiennes
    if 'daily' in data and 'temperature_2m_min' in data['daily'] and 'temperature_2m_max' in data['daily']:
        daily_times = pd.to_datetime(data['daily']['time'])
        df_daily = pd.DataFrame({
            "date": daily_times,
            "temperature_min": data['daily']['temperature_2m_min'],
            "temperature_max": data['daily']['temperature_2m_max'],
            "sunrise": data['daily']['sunrise'],
            "sunset": data['daily']['sunset'],
            "windspeed_10m_max": data['daily']['windspeed_10m_max'],
            "windspeed_10m_min": data['daily']['windspeed_10m_min']
        })
        df_daily = df_daily.astype({
            "temperature_min": float,
            "temperature_max": float,
            "windspeed_10m_max": float,
            "windspeed_10m_min": float
        })
        return df_daily
    
    raise ValueError("Données quotidiennes manquantes dans la réponse de l'API")

#---------------------------------- Stockage des données dans la base de données ----------------------------------
def store_forecast_in_db(transcription: str, location: str, forecast_days: int, forecast_df: pd.DataFrame, mode: str):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "transcription": transcription,
        "city": location,
        "forecast_days": forecast_days,
        "forecast": forecast_df.to_dict(orient="records"),
        "mode": mode
    }
    logs.append(entry)
    try:
        import psycopg2
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ,
                transcription TEXT,
                city TEXT,
                forecast_days INTEGER,
                forecast JSONB,
                mode TEXT
            );
        """)
        cur.execute("""
            INSERT INTO forecasts (timestamp, transcription, city, forecast_days, forecast, mode)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (entry["timestamp"], entry["transcription"], entry["city"], entry["forecast_days"], json.dumps(entry["forecast"]), entry["mode"]))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors du stockage en base de données : {e}")

#---------------------------------- Monitoring ----------------------------------
def monitoring():
    try:
        import psycopg2
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, method, endpoint, http_status FROM request_logs
            ORDER BY timestamp DESC
        """)
        logs = cur.fetchall()
        cur.close()
        conn.close()
        return logs
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des logs de monitoring : {e}")
        return []

#---------------------------------- Stockage des logs de requête ----------------------------------
def store_request_log(method: str, endpoint: str, http_status: int):
    try:
        import psycopg2
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                method TEXT,
                endpoint TEXT,
                http_status INTEGER
            );
        """)
        cur.execute("""
            INSERT INTO request_logs (method, endpoint, http_status)
            VALUES (%s, %s, %s)
        """, (method, endpoint, http_status))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors du stockage du log de requête : {e}")


