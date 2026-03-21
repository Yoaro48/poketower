from email.mime import base

import pandas as pd
import requests


def crear_base_datos():
    pokemon_list = []
    print("Descargando")
    for i in range(1,1010):
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{i}").json()
        pokemon_list.append({
            "id": res["id"],
            "name": res["name"],
            "weight": res["weight"],
            "height": res["height"],
            "image": res["sprites"]["other"]["official-artwork"]["front_default"],
            "base_hp": res["stats"][0]["base_stat"],
            "base_attack": res["stats"][1]["base_stat"],
            "base_defense": res["stats"][2]["base_stat"],
            "base_special_defense": res["stats"][4]["base_stat"],
            "base_speed": res["stats"][5]["base_stat"],
            "base_special_attack": res["stats"][3]["base_stat"],
            "base_stat_total": sum([stat["base_stat"] for stat in res["stats"]])
    })

    df = pd.DataFrame(pokemon_list)
    df.to_csv("../pokemon.csv",index=False)
    print("Exportado con exito")


if __name__ == "__main__":
    crear_base_datos()