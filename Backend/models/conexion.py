class Conexion:
    def __init__(self, origen, destino, capacidad):
        self.origen = origen
        self.destino = destino
        self.capacidad = capacidad
        self.estado = "activo"  # Estado inicial "activo", puede cambiar a "obstruido"
