from functools import wraps
import logging
import time
from typing import Callable
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import features as features
from prometheus_client import Counter, Histogram

app = FastAPI()
REQUEST_COUNT = Counter("http_requests_total", "Nombre total de requêtes HTTP", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Durée des requêtes HTTP (en secondes)", ["method", "endpoint"])
ERRORS_COUNT = Counter("errors_total", "Nombre total d'erreurs survenues")
FORECAST_REQUESTS = Counter("forecast_requests_total", "Nombre total de demandes de prévisions traitées")


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

#---------------------------------- Reconnaissance  ----------------------------------
@app.get("/reconnaissance")
def reconnaissance():
    return features.recognize_from_microphone()

#--------- Extraction Entités ---------
@app.get("/extraction_entites")
def extraction_entites(text):
    return features.spacy_analyze(text)

#--------- Extraction Entités Ville ---------
@app.get("/extraction_entites_ville")
def extraction_entites_ville(text):
    return features.extract_entities_ville(text)

#--------- Extraction Entités Jours ---------
@app.get("/extraction_entites_jours")
def extraction_entites_jours(text):
    return features.extract_forecast_days(text)


#---------------------------------- Météo ----------------------------------
@app.get("/meteo_prevision")
def meteo(city_name: str, transcription: str = "", mode: str = ""):
    forecast_df = features.get_weather_forecast(city_name)
    if forecast_df is not None:
        features.store_forecast_in_db(transcription, city_name, len(forecast_df), forecast_df, mode)
    return forecast_df

@app.get("/meteo_prevision_horaire")
def meteo_horaire(city_name: str, transcription: str = "", mode: str = ""):
    forecast_df = features.get_hourly_weather_forecast(city_name)
    if forecast_df is not None:
        features.store_forecast_in_db(transcription, city_name, len(forecast_df), forecast_df, mode)
    return forecast_df

@app.get("/meteo_prevision_journaliere")
def meteo_journaliere(city_name: str, transcription: str = "", mode: str = ""):
    forecast_df = features.get_daily_weather_forecast(city_name)
    if forecast_df is not None:
        features.store_forecast_in_db(transcription, city_name, len(forecast_df), forecast_df, mode)
    return forecast_df



#---------------------------------- Monitoring ----------------------------------
@app.get("/monitoring")
def monitoring():
    return features.monitoring()

# Middleware Prometheus
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    elapsed_time = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, http_status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(elapsed_time)
    features.store_request_log(request.method, request.url.path, response.status_code)
    return response

def measure_latency(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        logging.info(f"Temps d'exécution de {func.__name__} : {time.time() - start:.2f} secondes")
        return result
    return wrapper

class WeatherResponse(BaseModel):
    location: str
    forecast: dict
    forecast_days: int
    message: str = None
    transcription: str = None
    mode: str = None