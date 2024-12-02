from services.red_acueducto import RedDeAcueducto
from utils.archivos import cargar_json

class ControladorRedDeAcueducto:
    def __init__(self):
        self.red = RedDeAcueducto()

    def cargar_red(self, ruta_archivo):
        self.red.cargar_red_desde_json(ruta_archivo)

    def simular_obstruccion(self, origen, destino):
        self.red.simular_obstruccion(origen, destino)

    def obtener_rutas_alternativas(self, origen, destino):
        return self.red.rutas_alternativas(origen, destino)
