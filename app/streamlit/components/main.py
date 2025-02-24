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
    ville = features.extract_entities_ville(ville)
    return features.get_coordinates(ville)

@app.get("/horizon")
def horizon(ville):
    return features.horizon(ville)

@app.get("/meteo")
def meteo():
    return features.get_weather()

@app.get("/meteo_prevision")
def meteo_prevision():
    return features.get_weather_forecast()

@app.get("/monitoring")
def monitoring():
    return features.monitoring()
