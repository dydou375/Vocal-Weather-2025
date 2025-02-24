from fastapi import FastAPI
import features


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/reconnaissance")
def reconnaissance():
    return features.recognize_from_microphone()

@app.get("/ville")
def ville(ville):
    #text
    return features.extract_entities_ville(ville)

@app.get("/ville_coordonnees")
def ville_coordonnees(ville):
    return features.get_coordinates(ville)

@app.get("/horizon_date")
def horizon(ville):
    return features.horizon(ville)

@app.get("/meteo_prevision")
def meteo(ville):
    return features.get_weather_forecast(ville)

@app.get("/monitoring")
def monitoring():
    return features.monitoring()
