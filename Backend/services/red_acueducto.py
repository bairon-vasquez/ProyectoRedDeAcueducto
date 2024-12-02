import networkx as nx
from Backend.models.barrio import Barrio
from Backend.models.tanque import Tanque
from Backend.models.conexion import Conexion

class RedDeAcueducto:
    def __init__(self):
        self.grafo = nx.DiGraph()  # Grafo dirigido para representar la red

    def agregar_tanque(self, id_tanque, capacidad):
        self.grafo.add_node(id_tanque, tipo="tanque", capacidad=capacidad, capacidad_actual=0)

    def agregar_barrio(self, id_barrio, demanda):
        self.grafo.add_node(id_barrio, tipo="barrio", demanda=demanda)

    def agregar_conexion(self, origen, destino, capacidad):
        self.grafo.add_edge(origen, destino, capacidad=capacidad, estado="activo")

    def cargar_red_desde_json(self, ruta_archivo):
        import json
        with open(ruta_archivo, 'r') as archivo:
            data = json.load(archivo)

        for tanque in data["tanques"]:
            self.agregar_tanque(tanque["id"], tanque["capacidad"])

        for barrio in data["barrios"]:
            self.agregar_barrio(barrio["id"], barrio["demanda"])

        for conexion in data["conexiones"]:
            self.agregar_conexion(conexion["origen"], conexion["destino"], conexion["capacidad"])

    def simular_obstruccion(self, origen, destino):
        if self.grafo.has_edge(origen, destino):
            self.grafo[origen][destino]["estado"] = "obstruido"

    def rutas_alternativas(self, origen, destino):
        def peso_nodo(u, v, d):
            return d["capacidad"] if d["estado"] == "activo" else float('inf')

        try:
            return nx.shortest_path(self.grafo, origen, destino, weight=peso_nodo)
        except nx.NetworkXNoPath:
            return None

    def optimizar_red(self):
        nuevas_conexiones = []
        for nodo in self.grafo.nodes:
            for vecino in self.grafo.nodes:
                if nodo != vecino and not self.grafo.has_edge(nodo, vecino):
                    nuevas_conexiones.append((nodo, vecino))
        return nuevas_conexiones
