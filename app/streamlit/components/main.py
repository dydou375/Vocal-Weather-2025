from fastapi import FastAPI
import features as features
import extract_date as extract_date


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

#---------------------------------- Reconnaissance  ----------------------------------
@app.get("/reconnaissance")
def reconnaissance():
    return features.recognize_from_microphone()

#---------------------------------- Ville (Extraction Entités)  ----------------------------------
@app.get("/ville")
def ville(text):
    return features.extract_entities_ville(text)

#---------------------------------- Période (Extraction Entités)  ----------------------------------
@app.get("/periode")
def periode(text):
    return extract_date.extract_dates(text)

#---------------------------------- Ville (Coordonnées Version 1)  ----------------------------------
@app.get("/ville_coordonnees_V1")
def ville_coordonnees_V1(ville):
    return features.get_coordinates_test(ville)

#---------------------------------- Ville (Coordonnées Version 2)  ----------------------------------
@app.get("/ville_coordonnees_V2")
def ville_coordonnees_V2(ville):
    return features.get_coordinates(ville)

#---------------------------------- Météo ----------------------------------
@app.get("/meteo_prevision")
def meteo(city_name):
    return features.get_weather_forecast(city_name)

#---------------------------------- Météo SEB ----------------------------------
@app.get("/meteo_prevision_seb")
def meteo_seb(city_name):
    return features.get_weather_forecast_seb(city_name)

#---------------------------------- Monitoring ----------------------------------
@app.get("/monitoring")
def monitoring():
    return features.monitoring()
