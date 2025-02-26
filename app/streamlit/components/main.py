from fastapi import FastAPI
import features as features


app = FastAPI()

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

# #---------------------------------- Ville (Extraction Entités)  ----------------------------------
# @app.get("/ville")
# def ville(text):
#     return features.extract_entities_ville(text)

# #---------------------------------- Ville (Coordonnées)  ----------------------------------
# @app.get("/ville_coordonnees")
# def ville_coordonnees(ville):
#     return features.get_coordinates(ville)

#---------------------------------- Météo ----------------------------------
@app.get("/meteo_prevision")
def meteo(city_name):
    return features.get_weather_forecast(city_name)

#---------------------------------- Monitoring ----------------------------------
@app.get("/monitoring")
def monitoring():
    return features.monitoring()
