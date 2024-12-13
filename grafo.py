import json #para guardar y cargar datos de la red de agua en formato json
import networkx as nx # para modelar y trabajar con la der de agua como un grafo dirigido
import matplotlib.pyplot as plt #para visualizar el grafo de la red de agua
import heapq #para gestionar colas de prioridad de calculos de flujo 
from collections import deque #para gesionar estructuras de datos FIFO util para recorridos en la red

class RedDeAgua:
    def __init__(self, archivo_json="red_agua.json"): #inicializa una instancia de la clase Red_de_agua
        self.grafo = nx.DiGraph()  #configura un grafo dirigido para representar la red
        self.archivo_json = archivo_json #especifica el archivo json para guardar los datos

    # Agregar casa con demanda de agua, si esta no esta ya en los nodos del grafo, y lo guarda
    def agregar_casa(self, casa, demanda):
        if casa not in self.grafo.nodes:
            self.grafo.add_node(casa, tipo="casa", demanda=demanda)
            self.guardar_en_json()
        else:
            print(f"La casa {casa} ya existe en la red.")
            
    #elimina una casa si existe en los nodos del grafo y lo guarda
    def eliminar_casa(self, casa):
        if casa in self.grafo.nodes and self.grafo.nodes[casa]["tipo"] == "casa":
            self.grafo.remove_node(casa)
            print(f"La casa {casa} ha sido eliminada.")
            self.guardar_en_json()
        else:
            print(f"La casa {casa} no existe en la red.")
            
    #agrega un tanque con capacidad y sus respectivas conexiones, inicializa el nivel=capacidad y le resta la capacidad
    #de flujo de las tuberias conectadas en sentido saliente del tanque, y lo guarda en el json
    def agregar_tanque_con_capacidad(self, nombre, capacidad, conexiones):
        if nombre in self.grafo.nodes:
            print(f"El tanque {nombre} ya existe en la red.")
            return

        # El nivel inicial será igual a la capacidad del tanque
        nivel_inicial = capacidad
        self.grafo.add_node(nombre, tipo="tanque", capacidad=capacidad, nivel=nivel_inicial)

        for nodo in conexiones:
            if nodo in self.grafo.nodes:
                self.agregar_tuberia(nombre, nodo, capacidad_flujo=0)

                # Restar la capacidad de flujo de la tubería al nivel del tanque
                self.grafo.nodes[nombre]["nivel"] -= self.grafo.edges[nombre, nodo]["capacidad_flujo"]
            else:
                print(f"El nodo {nodo} no existe. No se pudo agregar la conexión.")

        self.guardar_en_json()
        
    #elimina un tanque si este esta en los nodos del grafo y se guarda el json
    def eliminar_tanque(self, tanque):
        if tanque in self.grafo.nodes and self.grafo.nodes[tanque]["tipo"] == "tanque":
            self.grafo.remove_node(tanque)
            print(f"El tanque {tanque} ha sido eliminado.")
            self.guardar_en_json()
        else:
            print(f"El tanque {tanque} no existe en la red.")
    
    #Agrega una tubería entre dos nodos y distribuye el flujo entre ellos.
    def agregar_tuberia(self, nodo1, nodo2, capacidad_flujo):
        if nodo1 in self.grafo.nodes and nodo2 in self.grafo.nodes:
            self.grafo.add_edge(nodo1, nodo2, capacidad_flujo=capacidad_flujo)
            print(f"Tubería agregada de {nodo1} a {nodo2} con capacidad de flujo {capacidad_flujo} L/s.")
            
            if self.grafo.nodes[nodo1]["tipo"] == "tanque":
                self.actualizar_nivel_tanque(nodo1)
                
            # Realizar el recorrido de flujo y verificar si la demanda de las casas está siendo suplida
            if self.grafo.nodes[nodo2]["tipo"] == "casa":
                self.verificar_y_distribuir_flujo(nodo1, nodo2, capacidad_flujo)
                
            #si el nodo2 es un tanque, calcula cuanta agua le vuelve a llegar despues de hacer el recorrido por las casas
            if self.grafo.nodes[nodo2]["tipo"] == "tanque":
                flujo_disponible = capacidad_flujo
                
                # Recorrer las casas previas y restar su demanda
                for casa in self.grafo.predecessors(nodo2):
                    if self.grafo.nodes[casa]["tipo"] == "casa":
                        demanda_casa = self.grafo.nodes[casa]["demanda"]
                        flujo_disponible -= min(demanda_casa, flujo_disponible)
                
                # Si el flujo restante es positivo, se suma al tanque
                if flujo_disponible > 0:
                    self.grafo.nodes[nodo2]["nivel"] += flujo_disponible
                    print(f"El tanque {nodo2} ha recibido {flujo_disponible} L/s. Nivel actual: {self.grafo.nodes[nodo2]['nivel']} L.") 

            self.guardar_en_json()

            # Después de agregar todas las tuberías, recalcular el flujo total
            self.calcular_distribucion_flujo()  # Esto asegura que todos los flujos se distribuyan correctamente
        else:
            print("Uno o ambos nodos no existen en la red.")
            
    #Verifica si la demanda de la casa destino está siendo suplida por el flujo de la tubería
    #y distribuye el flujo sobrante a la siguiente casa. Si no está siendo suplida correctamente,
    #se devuelve una sugerencia de solución.
    def verificar_y_distribuir_flujo(self, nodo_origen, nodo_destino, capacidad_flujo):
        # Obtener la demanda de la casa
        demanda = self.grafo.nodes[nodo_destino]["demanda"]

        # Calcular el flujo entrante a la casa sumando todas las tuberías que llegan
        flujo_disponible = sum(self.grafo[nodo][nodo_destino]["capacidad_flujo"] for nodo, _ in self.grafo.in_edges(nodo_destino))

        print(f"Casa {nodo_destino} - Demanda: {demanda}, Flujo Entrante: {flujo_disponible}")

        # Si el flujo entrante es suficiente para cubrir la demanda
        if flujo_disponible >= demanda:
            flujo_utilizado = demanda  # El flujo utilizado es igual a la demanda
            flujo_sobrante = flujo_disponible - flujo_utilizado  # El sobrante es lo que queda después de cubrir la demanda
            print(f"Casa {nodo_destino} - Flujo Utilizado: {flujo_utilizado}, Sobrante: {flujo_sobrante}")

            # Si hay un sobrante, distribuirlo a la siguiente casa
            if flujo_sobrante > 0:
                # Llamamos de nuevo a la función para distribuir el flujo sobrante a la siguiente casa
                self.distribuir_sobrante_a_siguiente_casa(nodo_destino, flujo_sobrante)

        else:
            print(f"La demanda de la casa {nodo_destino} NO está siendo suplida adecuadamente.")
            # Si el flujo es insuficiente, devolver un mensaje de advertencia
            sugerencia = f"Se recomienda agregar un tanque conectado a {nodo_destino}."
            return sugerencia  # Devolver la sugerencia
        
        return None  # Si no hay sugerencia, devolver None
    
    # Distribuye el flujo sobrante a la siguiente casa o tanque en la red.
    def distribuir_sobrante_a_siguiente_casa(self, nodo, flujo_sobrante):
        for _, vecino in self.grafo.out_edges(nodo):
            capacidad_tuberia = self.grafo[nodo][vecino]["capacidad_flujo"]

            if capacidad_tuberia > 0:  # Solo distribuir si la tubería tiene capacidad
                if self.grafo.nodes[vecino]["tipo"] == "tanque":
                    # Si el flujo va a un tanque, actualizamos su nivel
                    print(f"Devolviendo {flujo_sobrante} L/s al tanque {vecino}.")
                    self.grafo.nodes[vecino]["nivel"] += flujo_sobrante
                    return  # El flujo sobrante se devuelve al tanque y terminamos
                elif self.grafo.nodes[vecino]["tipo"] == "casa":
                    # Si el flujo va a una casa, calculamos cuánto necesita
                    demanda_vecino = self.grafo.nodes[vecino]["demanda"]
                    flujo_a_enviar = min(flujo_sobrante, demanda_vecino)

                    flujo_sobrante -= flujo_a_enviar  # Reducir el sobrante en lo enviado
                    print(f"Distribuyendo {flujo_a_enviar} L/s a {vecino}. Flujo sobrante restante: {flujo_sobrante}")

                    # Continuar distribuyendo el sobrante si queda
                    if flujo_sobrante > 0:
                        self.distribuir_sobrante_a_siguiente_casa(vecino, flujo_sobrante)
                        
            #se edita la capacidad de la tuberia ingresando un porcentaje de reduccion
    def editar_tuberia(self, nodo1, nodo2, nueva_obstruccion):
        if self.grafo.has_edge(nodo1, nodo2):
            # Validar obstrucción
            if nueva_obstruccion == -1:
                capacidad_reducida = 0  # Obstrucción total
            elif 0 <= nueva_obstruccion <= 100:
                capacidad_original = self.grafo[nodo1][nodo2]['capacidad_flujo']
                capacidad_reducida = capacidad_original * (1 - nueva_obstruccion / 100)
            else:
                print("Error: El porcentaje de obstrucción debe estar entre 0 y 100 o ser -1 para obstrucción total.")
                return
            
            # Calcular la diferencia en el flujo debido a la obstrucción
            flujo_perdido = self.grafo[nodo1][nodo2]['capacidad_flujo'] - capacidad_reducida
            
            # Actualizar atributos del borde
            self.grafo[nodo1][nodo2]['capacidad_flujo'] = capacidad_reducida
            self.grafo[nodo1][nodo2]['obstruccion'] = nueva_obstruccion

            print(f"Tubería de {nodo1} a {nodo2} actualizada con nueva capacidad de {capacidad_reducida:.2f} L/s y obstrucción {nueva_obstruccion}%.")
            self.guardar_en_json()
            
            # Si el nodo de origen es un tanque, devolver el flujo perdido al tanque
            if self.grafo.nodes[nodo1]["tipo"] == "tanque":
                tanque = self.grafo.nodes[nodo1]
                tanque["nivel"] += flujo_perdido
                print(f"El tanque {nodo1} recuperó {flujo_perdido:.2f} L de agua. Nuevo nivel: {tanque['nivel']}L.")
            
            # Guardar los cambios en el archivo JSON
            self.guardar_en_json()
        else:
            print("Error: La tubería especificada no existe en el grafo.")
            
        #Elimina la tubería entre dos nodos, recalcula el nivel de los tanques
        #y verifica la distribución del flujo.
    def eliminar_tuberia(self, nodo1, nodo2):
        if self.grafo.has_edge(nodo1, nodo2):
            # Eliminar la tubería
            self.grafo.remove_edge(nodo1, nodo2)
            print(f"La tubería entre {nodo1} y {nodo2} ha sido eliminada.")

            # Recalcular el nivel de los tanques afectados
            for nodo in self.grafo.nodes:
                if self.grafo.nodes[nodo]["tipo"] == "tanque":
                    self.actualizar_nivel_tanque(nodo)  # Usamos el método existente para actualizar el nivel

            # Verificar y recalcular la distribución de flujo
            flujo_disponible = self.calcular_distribucion_flujo()

            # Verificar si hay casas sin suficiente flujo
            for nodo, flujo in flujo_disponible.items():
                if self.grafo.nodes[nodo]["tipo"] == "casa":
                    if flujo < self.grafo.nodes[nodo]["demanda"]:
                        print(f"La casa {nodo} no tiene suficiente flujo. Se recomienda redistribuir el flujo.")

            # Guardar cambios en el JSON
            self.guardar_en_json()
        else:
            print(f"No existe una tubería entre {nodo1} y {nodo2}.")

    # Cargar datos desde archivo JSON
    def cargar_desde_json(self, archivo):
        with open(archivo, 'r') as f:
            datos = json.load(f)

        for casa, info in datos.get("casas", {}).items():
            self.agregar_casa(casa, info["demanda"])
        for tanque, info in datos.get("tanques", {}).items():
            self.agregar_tanque_con_capacidad(tanque, info["capacidad"], info["conexiones"])
        for tuberia in datos.get("tuberias", []):
            self.agregar_tuberia(tuberia["nodo1"], tuberia["nodo2"], tuberia["capacidad_flujo"])

    # Guardar estado actual en archivo JSON
    def guardar_en_json(self):
        datos = {
            "casas": {
                nodo: {"demanda": data["demanda"]}
                for nodo, data in self.grafo.nodes(data=True) if data["tipo"] == "casa"
            },
            "tanques": {
                nodo: {
                    "capacidad": data["capacidad"],
                    "nivel": data["nivel"],  # Aquí agregamos el nivel del tanque
                    "conexiones": list(self.grafo.neighbors(nodo))
                }
                for nodo, data in self.grafo.nodes(data=True) if data["tipo"] == "tanque"
            },
            "tuberias": [
                {"nodo1": u, "nodo2": v, "capacidad_flujo": datos["capacidad_flujo"]}
                for u, v, datos in self.grafo.edges(data=True)
            ]
        }
        with open(self.archivo_json, 'w') as f:
            json.dump(datos, f, indent=4)
        print(f"Datos guardados en {self.archivo_json}")
    
    def actualizar_nivel_tanque(self, tanque):
        if tanque in self.grafo.nodes and self.grafo.nodes[tanque]["tipo"] == "tanque":
            # Reiniciar el nivel al máximo (capacidad del tanque)
            nivel_actual = self.grafo.nodes[tanque]["capacidad"]

            # Iterar sobre las conexiones desde el tanque
            for _, destino in self.grafo.out_edges(tanque):
                # Restar la capacidad de flujo de cada tubería conectada
                capacidad_flujo = self.grafo[tanque][destino].get("capacidad_flujo", 0)
                nivel_actual -= capacidad_flujo

            # Asegurar que el nivel no sea negativo
            self.grafo.nodes[tanque]["nivel"] = max(0, nivel_actual)
            print(f"El nivel del tanque '{tanque}' se actualizó a {nivel_actual}.")
        else:
            print(f"El nodo '{tanque}' no es un tanque o no existe en la red.")
            
        #Verifica si las tuberías que alimentan a una casa satisfacen su demanda de agua.
        #Retorna True si la demanda es satisfecha, False en caso contrario.
    def verificar_demanda_casa(self, casa):
        if casa in self.grafo.nodes and self.grafo.nodes[casa]["tipo"] == "casa":
            demanda = self.grafo.nodes[casa]["demanda"]
            flujo_total = 0

            # Sumar la capacidad de flujo de todas las tuberías que llegan a la casa
            for origen, _ in self.grafo.in_edges(casa):
                flujo_total += self.grafo[origen][casa].get("capacidad_flujo", 0)

            if flujo_total >= demanda:
                print(f"La demanda de la casa '{casa}' está satisfecha ({flujo_total}/{demanda}).")
                return True
            else:
                print(f"La demanda de la casa '{casa}' NO está satisfecha ({flujo_total}/{demanda}).")
                return False
        else:
            print(f"El nodo '{casa}' no es una casa o no existe en la red.")
            return False
        
        #Calcula la distribución de flujo en la red, verificando excedentes en cada nodo.
    def calcular_distribucion_flujo(self):
        flujo_disponible = {nodo: 0 for nodo in self.grafo.nodes}

        # Inicializar los tanques con su nivel inicial como flujo disponible
        for nodo, data in self.grafo.nodes(data=True):
            if data["tipo"] == "tanque":
                flujo_disponible[nodo] = data["nivel"]

        # Realizar un recorrido BFS desde los tanques
        visitados = set()
        cola = [nodo for nodo, data in self.grafo.nodes(data=True) if data["tipo"] == "tanque"]

        while cola:
            nodo_actual = cola.pop(0)
            if nodo_actual in visitados:
                continue

            visitados.add(nodo_actual)

            # Calcular el flujo entrante al nodo actual
            flujo_entrante = flujo_disponible[nodo_actual]

            # Si es una casa, consumir la demanda
            if self.grafo.nodes[nodo_actual]["tipo"] == "casa":
                demanda = self.grafo.nodes[nodo_actual]["demanda"]
                flujo_utilizado = min(flujo_entrante, demanda)
                flujo_disponible[nodo_actual] -= flujo_utilizado

            # Redistribuir el flujo sobrante a los nodos vecinos
            flujo_sobrante = flujo_disponible[nodo_actual]

            for _, vecino in self.grafo.out_edges(nodo_actual):
                capacidad_tuberia = self.grafo[nodo_actual][vecino]["capacidad_flujo"]
                flujo_a_enviar = min(flujo_sobrante, capacidad_tuberia)

                flujo_disponible[vecino] += flujo_a_enviar
                flujo_disponible[nodo_actual] -= flujo_a_enviar

                if vecino not in visitados:
                    cola.append(vecino)

        return flujo_disponible
    
    #Verifica el suministro de agua para todas las casas y devuelve un resumen detallado.
    def verificar_suministro(self):
            resultados = {}

            for nodo, data in self.grafo.nodes(data=True):
                if data["tipo"] == "casa":
                    if not self.esta_conectada_a_tanque(nodo):
                        resultados[nodo] = {
                            "mensaje": "No está conectada a un tanque.",
                            "flujo_recibido": 0,
                            "demanda": data["demanda"]
                        }
                        continue

                    # Calcular el flujo recibido
                    flujo_recibido = sum(
                        self.grafo[origen][nodo]["capacidad_flujo"]
                        for origen, _ in self.grafo.in_edges(nodo)
                        if self.grafo[origen][nodo]["capacidad_flujo"] > 0
                    )

                    # Verificar si el flujo recibido es suficiente
                    if flujo_recibido >= data["demanda"]:
                        resultados[nodo] = {
                            "mensaje": "Suministro completo.",
                            "flujo_recibido": flujo_recibido,
                            "demanda": data["demanda"]
                        }
                    else:
                        resultados[nodo] = {
                            "mensaje": "No tiene suficiente agua.",
                            "flujo_recibido": flujo_recibido,
                            "demanda": data["demanda"]
                        }
            return resultados
        
        
        #Verifica si el nodo está conectado a un tanque, directa o indirectamente.
    def esta_conectada_a_tanque(self, nodo):
        # Obtener todos los tanques del grafo
        tanques = [n for n, d in self.grafo.nodes(data=True) if d["tipo"] == "tanque"]

        # Verificar si existe un camino desde algún tanque hasta el nodo
        for tanque in tanques:
            if nx.has_path(self.grafo, tanque, nodo):
                return True
        return False
    
    def buscar_ruta_alternativa_optima(self, casa_afectada):
        if casa_afectada not in self.grafo.nodes or self.grafo.nodes[casa_afectada]["tipo"] != "casa":
            raise ValueError(f"El nodo {casa_afectada} no es una casa válida.")
        
        demanda = self.grafo.nodes[casa_afectada]["demanda"]
        flujo_maximo = {nodo: 0 for nodo in self.grafo.nodes}
        rutas = {nodo: [] for nodo in self.grafo.nodes}
        
        # Iniciar la cola de prioridad
        pq = [(0, casa_afectada)]  
        flujo_maximo[casa_afectada] = float('inf')
        rutas[casa_afectada] = [casa_afectada]
        
        while pq:
            _, nodo_actual = heapq.heappop(pq)
            
            for vecino in self.grafo.predecessors(nodo_actual):
                datos_arista = self.grafo[vecino][nodo_actual]
                capacidad_flujo = datos_arista.get("capacidad_flujo", 0)
                obstruccion = datos_arista.get("obstruccion", 0)
                
                if obstruccion == -1 or capacidad_flujo == 0:
                    continue
                
                # Calcular flujo ajustado
                capacidad_ajustada = capacidad_flujo * (1 - obstruccion / 100)
                flujo_disponible = min(flujo_maximo[nodo_actual], capacidad_ajustada)
                
                if flujo_disponible > flujo_maximo[vecino]:
                    flujo_maximo[vecino] = flujo_disponible
                    rutas[vecino] = rutas[nodo_actual] + [vecino]
                    heapq.heappush(pq, (-flujo_disponible, vecino))
        
        # Buscar el tanque más cercano que pueda suplir
        for tanque in [nodo for nodo, datos in self.grafo.nodes(data=True) if datos["tipo"] == "tanque"]:
            if flujo_maximo[tanque] >= demanda:
                return rutas[tanque][::-1] + [casa_afectada], flujo_maximo[tanque]
        
        return None, 0
    
        #Cambia el sentido de una tubería en la red.
        #Si el nuevo destino es un tanque, ajusta su nivel con el flujo disponible en el nodo origen.
        #También actualiza el JSON para reflejar el nuevo orden de los nodos.
    def cambiar_sentido_tuberia(self, nodo1, nodo2):
        if not self.grafo.has_edge(nodo1, nodo2):
            print("La tubería no existe en esta dirección.")
            return

        # Obtener la capacidad de la tubería
        capacidad_flujo = self.grafo[nodo1][nodo2]["capacidad_flujo"]

        # Eliminar la tubería actual del grafo
        self.grafo.remove_edge(nodo1, nodo2)

        # Agregar la tubería en la dirección opuesta
        self.grafo.add_edge(nodo2, nodo1, capacidad_flujo=capacidad_flujo)
        print(f"Tubería cambiada de dirección: {nodo1} -> {nodo2} ahora es {nodo2} -> {nodo1}.")

        # Actualizar el JSON
        with open(self.archivo_json, 'r') as f:
            datos = json.load(f)

        # Buscar y actualizar la tubería en el JSON
        tuberias = datos.get("tuberias", [])
        tuberia_a_eliminar = None
        for tuberia in tuberias:
            if tuberia["nodo1"] == nodo1 and tuberia["nodo2"] == nodo2:
                tuberia_a_eliminar = tuberia
                break
        
        if tuberia_a_eliminar:
            tuberias.remove(tuberia_a_eliminar)  # Eliminar la tubería original
            # Agregar la tubería con el nuevo orden
            tuberias.append({"nodo1": nodo2, "nodo2": nodo1, "capacidad_flujo": capacidad_flujo})
        
        # Guardar los cambios en el JSON
        datos["tuberias"] = tuberias
        with open(self.archivo_json, 'w') as f:
            json.dump(datos, f, indent=4)

        # Recargar el grafo para reflejar los cambios
        self.cargar_desde_json(self.archivo_json)
        
        #Verifica si hay conexiones duplicadas en el grafo y devuelve los mensajes.
    def verificar_conexiones_duplicadas(self):
        mensajes = []
        for nodo1, nodo2 in self.grafo.edges:
            if self.grafo.has_edge(nodo2, nodo1):  # Si ya existe la conexión en la dirección opuesta
                mensajes.append(f"Conexión duplicada encontrada entre {nodo1} y {nodo2}.")
        return mensajes
    
    #Detecta bucles (ciclos) en la red de distribución de agua y devuelve los mensajes.
    def detectar_bucles(self):
        mensajes = []
        try:
            # Detectar ciclos en el grafo dirigido
            ciclos = list(nx.simple_cycles(self.grafo))
            if ciclos:
                for ciclo in ciclos:
                    mensajes.append(f"Se ha detectado un bucle en el flujo: {' -> '.join(ciclo)}.")
        except Exception as e:
            mensajes.append(f"Error al detectar ciclos: {e}")
        return mensajes

    #Verifica si hay conexiones duplicadas en el grafo y devuelve los mensajes.
    def verificar_conexiones_duplicadas(self):
        mensajes = []
        for nodo1, nodo2 in self.grafo.edges:
            if self.grafo.has_edge(nodo2, nodo1):  # Si ya existe la conexión en la dirección opuesta
                mensajes.append(f"Conexión duplicada encontrada entre {nodo1} y {nodo2}.")
        return mensajes

    #Detecta bucles (ciclos) en la red de distribución de agua y devuelve los mensajes.
    def detectar_bucles(self):
        mensajes = []
        try:
            # Detectar ciclos en el grafo dirigido
            ciclos = list(nx.simple_cycles(self.grafo))
            if ciclos:
                for ciclo in ciclos:
                    mensajes.append(f"Se ha detectado un bucle en el flujo: {' -> '.join(ciclo)}.")
        except Exception as e:
            mensajes.append(f"Error al detectar ciclos: {e}")
        return mensajes
    
    #Verifica si hay conexiones con nodos no definidos (por ejemplo, un tanque o barrio no existente).
    def verificar_conexiones_con_nodos_no_definidos(self):
        mensajes = []
        # Recorremos las conexiones
        for nodo1, nodo2 in self.grafo.edges:
            if nodo1 not in self.grafo.nodes or nodo2 not in self.grafo.nodes:
                mensajes.append(f"Conexión entre nodos no definidos: {nodo1} y {nodo2}.")
        return mensajes
    
    # Realiza una búsqueda en amplitud (BFS) para encontrar un camino aumentante.
    #Trabaja sobre una copia del grafo.
    def bfs(self, grafo, source, sink, parent):
        visited = set()
        queue = deque([source])
        visited.add(source)
        
        while queue:
            u = queue.popleft()
            
            for v in grafo.neighbors(u):
                if v not in visited and grafo[u][v].get('capacidad_flujo', 0) > 0:  # Hay capacidad residual
                    queue.append(v)
                    visited.add(v)
                    parent[v] = u
                    
                    # Si llegamos al sumidero, retornamos True
                    if v == sink:
                        return True
        return False

    #Implementa el algoritmo de Ford-Fulkerson para calcular el flujo máximo
    #desde el nodo 'source' hasta el nodo 'sink'.
    #Usamos una copia del grafo para evitar alteraciones durante el dibujo.
    def ford_fulkerson(self, source, sink):
        # Crear una copia del grafo para evitar modificar el grafo original
        grafo_copia = self.grafo.copy()

        parent = {}
        max_flow = 0
        
        # Mientras haya un camino aumentante, aumentamos el flujo
        while self.bfs(grafo_copia, source, sink, parent):
            # Encuentra el flujo máximo en el camino encontrado por BFS
            path_flow = float('Inf')
            s = sink
            
            while s != source:
                path_flow = min(path_flow, grafo_copia[parent[s]][s]['capacidad_flujo'])
                s = parent[s]
            
            # Actualiza las capacidades residuales de las aristas
            v = sink
            while v != source:
                u = parent[v]
                grafo_copia[u][v]['capacidad_flujo'] -= path_flow  # Disminuye la capacidad en el camino directo
                if v in grafo_copia and u in grafo_copia[v]:
                    grafo_copia[v][u]['capacidad_flujo'] += path_flow  # Aumenta la capacidad en el camino inverso
                else:
                    grafo_copia.add_edge(v, u, capacidad_flujo=path_flow)  # Añade una nueva arista en sentido inverso
                v = parent[v]
            
            max_flow += path_flow
        
        return max_flow
    
    #Recarga el archivo JSON y actualiza el grafo.
    def recargar_json(self):
        try:
            with open(self.archivo_json, 'r') as f:
                datos = json.load(f)

            # Limpiar el grafo actual
            self.grafo.clear()

            # Reconstruir el grafo desde el JSON
            for casa, info in datos.get("casas", {}).items():
                self.agregar_casa(casa, info["demanda"])
            for tanque, info in datos.get("tanques", {}).items():
                self.agregar_tanque_con_capacidad(tanque, info["capacidad"], info["conexiones"])
            for tuberia in datos.get("tuberias", []):
                self.agregar_tuberia(tuberia["nodo1"], tuberia["nodo2"], tuberia["capacidad_flujo"])

            print(f"Datos recargados desde {self.archivo_json}.")
        except Exception as e:
            print(f"Error al recargar JSON: {e}")
            
            #  Proponer nuevas conexiones entre tanques para mejorar la cobertura en caso de obstrucciones,
            #teniendo en cuenta las capacidades de los tanques y las restricciones de presión.
    def proponer_nuevas_conexiones(self):
        sugerencias = []
        
        # Obtener los tanques con capacidad disponible
        for tanque_origen, data_origen in self.grafo.nodes(data=True):
            if data_origen["tipo"] == "tanque" and self.es_presion_adecuada(data_origen):
                capacidad_disponible = data_origen["capacidad"] - data_origen["nivel"]
                
                # Buscar tanques posibles para conectar
                for tanque_destino, data_destino in self.grafo.nodes(data=True):
                    if tanque_origen != tanque_destino and data_destino["tipo"] == "tanque" and self.es_presion_adecuada(data_destino):
                        capacidad_adecuada = data_destino["capacidad"] - data_destino["nivel"]
                        
                        # Verificar si la conexión es posible según las capacidades
                        if capacidad_disponible <= capacidad_adecuada:
                            # Verificar si la presión es adecuada
                            if self.es_conexion_valida(tanque_origen, tanque_destino):
                                sugerencias.append(f"Conectar {tanque_origen} con {tanque_destino} para optimizar flujo.")
        
        # Retornar las sugerencias generadas
        return sugerencias
    #  Verificar si la presión del tanque es adecuada.
    # La presión es adecuada si el nivel está entre el 10% y el 90% de la capacidad.
    def es_presion_adecuada(self, tanque_data):
        nivel = tanque_data["nivel"]
        capacidad = tanque_data["capacidad"]
        
        # Umbrales para la presión inadecuada
        if nivel < capacidad * 0.1 or nivel > capacidad * 0.9:
            return False  # La presión no es adecuada
        return True
    
    #Verificar si una conexión entre dos tanques es válida según las capacidades y la presión de los tanques.
    def es_conexion_valida(self, tanque_origen, tanque_destino):
        # Obtener los datos de los tanques
        data_origen = self.grafo.nodes[tanque_origen]
        data_destino = self.grafo.nodes[tanque_destino]

        # Verificar que los tanques no estén sobrecargados o vacíos
        if not self.es_presion_adecuada(data_origen) or not self.es_presion_adecuada(data_destino):
            return False  # La conexión no es válida si la presión no es adecuada
        
        # Si la capacidad total no se sobrepasa, la conexión es válida
        capacidad_disponible = data_origen["capacidad"] - data_origen["nivel"]
        capacidad_adecuada = data_destino["capacidad"] - data_destino["nivel"]
        
        if capacidad_disponible > capacidad_adecuada:
            return False  # No se puede hacer la conexión si uno de los tanques está más lleno que el otro

        return True
    
        #Identificar casas que no están siendo abastecidas correctamente.
        #Usamos verificar_y_distribuir_flujo para detectar casas con demanda no cubierta.
    def identificar_casas_sin_servicio(self):
        casas_sin_servicio = []
        
        for casa, data in self.grafo.nodes(data=True):
            if data["tipo"] == "casa":
                sugerencia = self.verificar_y_distribuir_flujo(None, casa, None)  # Solo verificamos flujo, sin necesidad de origen/destino
                if sugerencia:  # Si la sugerencia no es None, significa que la casa no tiene suficiente agua
                    casas_sin_servicio.append(casa)
        
        return casas_sin_servicio
    
    # Agrupar casas sin servicio, es decir, casas que están conectadas y podrían abastecerse desde un solo tanque.
    def agrupar_casas_sin_servicio(self, casas_sin_servicio):
        grupos_casas = []
        casas_visitadas = set()
        
        # Iterar sobre las casas sin servicio
        for casa in casas_sin_servicio:
            if casa not in casas_visitadas:
                # Buscar las casas conectadas a esta casa en la red
                grupo = self.dfs_buscar_grupo(casa, casas_visitadas)
                grupos_casas.append(grupo)
        
        return grupos_casas
    
    # Realiza una búsqueda en profundidad (DFS) para encontrar todas las casas conectadas a una casa en particular
    # que no tienen suficiente suministro de agua.
    def dfs_buscar_grupo(self, casa, casas_visitadas):
        grupo = []
        stack = [casa]
        
        while stack:
            casa_actual = stack.pop()
            if casa_actual not in casas_visitadas:
                casas_visitadas.add(casa_actual)
                grupo.append(casa_actual)
                
                # Agregar casas conectadas
                for vecino in self.grafo.neighbors(casa_actual):
                    if vecino not in casas_visitadas:
                        stack.append(vecino)
        
        return grupo
    
    #Proponer la instalación de nuevos tanques para abastecer a los grupos de casas sin servicio.
    def proponer_nuevos_tanques(self, grupos_casas):
        sugerencias_tanques = []
        
        for grupo in grupos_casas:
            if grupo:
                # Suponemos que el primer nodo del grupo puede ser la ubicación del nuevo tanque
                tanque_sugerido = grupo[0]
                sugerencias_tanques.append(f"Instalar un nuevo tanque en {tanque_sugerido} para abastecer a las casas: {', '.join(grupo)}")
        
        return sugerencias_tanques
    