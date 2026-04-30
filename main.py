
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from enum import Enum
from datetime import date
import sqlite3
from passlib.context import CryptContext
import bcrypt

import os

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("About", (object,), {"__version__": bcrypt.__version__})

class UserAuth(BaseModel):
    username: str
    password: str = None

class Categoria(str, Enum):
    peso = "weight"
    altura = "height"
    ataque = "base_attack"
    defensa = "base_defense"

class PokemonSimplificado(BaseModel):
    id: int
    name: str
    image: str

class TowerChallenge(BaseModel):
    categoria_reto: Categoria
    pokemon_list: list[PokemonSimplificado]

import pandas as pd
import random

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Esto permite que cualquier web use tu API
    allow_methods=["*"],
    allow_headers=["*"],
)

df = pd.read_csv("pokemon.csv")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cambia esto en tu main.py
def get_db():
    # Usamos /app/data/ porque es donde montamos el volumen
    db_path = "/app/data/usuarios.db" 
    # Si estás probando en tu PC local, usa la ruta normal
    if not os.path.exists("/app/data"):
        db_path = "usuarios.db"
    
    conn = sqlite3.connect(db_path)
    return conn

def obtener_configuracion_hoy():
    hoy = date.today()
    semilla = int(hoy.strftime("%Y%m%d"))
    
    categorias_disp = list(Categoria)
    categoria = categorias_disp[semilla % len(categorias_disp)]
    
    return semilla, categoria

@app.get("/pokemon_difuminado")
def get_pokemon_difuminado(id: int):
    semilla, _ = obtener_configuracion_hoy()
    poke = df.sample(1, random_state=semilla+1)
    return 

@app.get("/get_tower", response_model=TowerChallenge)
def get_tower():
    # 1. Cogemos 5 al azar con Pandas
    semilla, categoria = obtener_configuracion_hoy()
    
    # 2. Usamos la semilla para que el sample de Pandas sea igual para todos hoy
    # Usamos random_state para fijar la semilla en Pandas
    sample = df.sample(10, random_state=semilla)
    
    # 2. Creamos la lista de objetos Pokemon
    lista_pokemon = []
    for _, row in sample.iterrows():
        lista_pokemon.append(
            PokemonSimplificado(id=row['id'], name=row['name'].capitalize(), image=row['image'])
        )
    
    # 3. Mezclamos para que no aparezcan ordenados por defecto
    random.seed(semilla)  # Fijamos la semilla para que el shuffle sea igual para todos hoy
    random.shuffle(lista_pokemon)

    # Cambia cada día
    # 4. Devolvemos el objeto Tower
    return TowerChallenge( # ID único para esta partida
        categoria_reto=categoria,
        pokemon_list=lista_pokemon
    )

@app.post("/verify")
def verify_order(user_order: List[str], tiempo: float, username: str = None):

    sufixes = {
        "weight": "kg", "height": "m", "base_attack": "atk",
        "base_defense": "def", "base_speed": "spe", "base_sp_attack": "spa",
        "base_sp_defense": "spd", "base_hp": "hp", "base_stat_total": "bst"
    }
    
    _, categoria = obtener_configuracion_hoy()
    
    # 1. Pasamos el orden del usuario a minúsculas estrictas
    user_order_lower = [name.lower() for name in user_order]
    
    # 2. Buscamos ignorando mayúsculas en el DataFrame
    datos_reales = df[df['name'].str.lower().isin(user_order_lower)].copy()

    datos_dicc = {row['name'].lower(): row[categoria.value] for _, row in datos_reales.iterrows()}

    # 3. Creamos una columna temporal 100% en minúsculas para el orden real
    datos_reales['name_lower'] = datos_reales['name'].str.lower()
    
    # Ordenamos
    datos_reales = datos_reales.sort_values(by=categoria.value, ascending=False)
    
    # 4. Extraemos el orden correcto también en minúsculas
    orden_correcto_lower = datos_reales['name_lower'].tolist()

    # 5. AHORA SÍ: Comparamos peras con peras (minúscula con minúscula) y sus valores en caso de que sea el mismo
    aciertos = [u == c or datos_dicc.get(u) == datos_dicc.get(c) for u, c in zip(user_order_lower, orden_correcto_lower)]

    # Info extra (mantenemos capitalize para que se vea bien en el HTML)
    info_extra = {row['name'].capitalize(): f"{row[categoria.value]}{sufixes.get(categoria.value, '')}" for _, row in datos_reales.iterrows()}
    
    # 6. La comprobación final debe ser con las dos listas en minúsculas
    if aciertos.count(False) == 0:
        submit_result(username=username, tiempo=tiempo, completado=True)
        return {"status": "correct", "message": "¡Increíble!", "info": info_extra, "aciertos": aciertos}
    else:
        return {"status": "wrong", "correct_order": orden_correcto_lower, "info": info_extra, "aciertos": aciertos}
    
@app.get("/leaderboard_racha")
def get_leaderboard_racha():
    conn = get_db()
    cursor = conn.cursor()
    # Todo el comando debe ir dentro del execute
    cursor.execute('SELECT username, mejor_racha FROM perfiles ORDER BY mejor_racha DESC')
    racha = cursor.fetchmany(5)
    conn.close()
    return [{"username": row[0], "racha_actual": row[1]} for row in racha]

@app.get("/leaderboard_tiempo")
def get_leaderboard_tiempo():
    conn = get_db()
    cursor = conn.cursor()
    tiempo = cursor.execute(
        'SELECT username, tiempo '
        'FROM tiempos WHERE fecha = date("now")'
        'ORDER BY tiempo ASC ').fetchmany(5)
    conn.close()
    return [{"username": row[0], "tiempo_hoy": row[1]} for row in tiempo]

@app.post("/submit_result")
def submit_result(tiempo: float, completado: bool,username: str = None):

    if not username or username.strip() == "" or username.lower() == "null":
        return {"message": "Jugador anonimo, resultado no guardado"}
    
    conn = get_db()
    cursor = conn.cursor()
    
    # La racha se actualiza mediante un trigger en la base de datos, así que aquí solo insertamos el resultado

    # Guardamos el tiempo
    cursor.execute('INSERT INTO tiempos (username, tiempo, completado,fecha) VALUES (?, ?, ?, date("now"))', (username, tiempo, 1 if completado else 0))
    
    conn.commit()
    conn.close()
    
    return {"message": "Resultado guardado correctamente"}

@app.post("/register")
def register(user_auth: UserAuth): # Cambiado a minúscula para evitar conflictos
    try:
        if not user_auth.password:
            return {"status": "error", "message": "Password required"}

        # Truncamos el string directamente ANTES de enviarlo a passlib
        # Usamos los primeros 71 caracteres para estar 100% seguros con el límite de 72 bytes
        password_segura = user_auth.password[:71]
        
        hashed = pwd_context.hash(password_segura)

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO perfiles (username, password_hash) VALUES (?, ?)", 
                  (user_auth.username, hashed))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        # Esto atrapará el error de la imagen y nos dará más info si falla
        return {"status": "error", "message": f"Error interno: {str(e)}"}

@app.post("/login")
def login(user_auth: UserAuth):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT password_hash, racha_actual, ultima_fecha_jugada FROM perfiles WHERE username=?", 
                  (user_auth.username,))
        user = c.fetchone()
        conn.close()

        if user:
            # Truncamos igual que en el registro
            password_segura = user_auth.password[:71]
            if pwd_context.verify(password_segura, user[0]):
                return {"status": "success", "racha": user[1], "ultima": user[2]}
        
        return {"status": "error", "message": "Credenciales inválidas"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get_streak")
def get_streak(username: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT racha_actual FROM perfiles WHERE username=?", (username,))
    racha = c.fetchone()
    if racha:
        return {"status": "success", "racha": racha[0]}
    return {"status": "error", "message": "Usuario no encontrado"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
