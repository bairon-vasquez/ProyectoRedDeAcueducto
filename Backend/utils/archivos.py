import json

def cargar_json(ruta_archivo):
    with open(ruta_archivo, 'r') as archivo:
        return json.load(archivo)

def guardar_json(ruta_archivo, datos):
    with open(ruta_archivo, 'w') as archivo:
        json.dump(datos, archivo, indent=4)
