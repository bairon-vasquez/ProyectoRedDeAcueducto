import sys
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QInputDialog, QMessageBox, QFileDialog, QDialog, QComboBox, QSpinBox, QLabel, QTextEdit
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from grafo import RedDeAgua

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        
        # Aristas resaltadas para mantener el estado
        self.aristas_resaltadas = set()

    def dibujar_grafo(self, grafo, ruta_alternativa=None):
        self.axes.clear()
        pos = nx.circular_layout(grafo.grafo)

        # Dibujar las aristas primero
        colores_aristas = {
            (u, v): (
                "red" if datos.get("obstruccion", 0) == -1 else
                "orange" if 0 < datos.get("obstruccion", 0) <= 100 else
                "blue"
            )
            for u, v, datos in grafo.grafo.edges(data=True)
        }

        # Resaltar la ruta alternativa y almacenar aristas resaltadas
        if ruta_alternativa:
            for i in range(len(ruta_alternativa) - 1):
                u, v = ruta_alternativa[i], ruta_alternativa[i + 1]
                if grafo.grafo.has_edge(u, v):
                    self.aristas_resaltadas.add((u, v))

        # Aplicar colores resaltados
        for arista in self.aristas_resaltadas:
            if arista in colores_aristas:
                colores_aristas[arista] = "green"

        nx.draw(
            grafo.grafo, pos, with_labels=False, ax=self.axes,
            edge_color=[colores_aristas.get((u, v), "blue") for u, v in grafo.grafo.edges]
        )

        # Dibujar los nodos con imágenes
        for nodo, data in grafo.grafo.nodes(data=True):
            x, y = pos[nodo]
            if data["tipo"] == "casa":
                self._agregar_imagen("casa.png", x, y)
            elif data["tipo"] == "tanque":
                self._agregar_imagen("tanque.png", x, y)
            
            # Agregar nombre debajo de cada nodo (casa o tanque)
            self.axes.text(x, y - 0.15, nodo, fontsize=10, ha='center')

        # Etiquetas de nodos
        etiquetas_nodos = {
            nodo: (
                f"Nivel: {data['nivel']}/{data['capacidad']}L" if data["tipo"] == "tanque" else
                f"Demanda: {data['demanda']}L/s"
            )
            for nodo, data in grafo.grafo.nodes(data=True)
        }

        # Ajustar las coordenadas para desplazar las etiquetas hacia arriba
        pos_labels = {nodo: (x, y + 0.1) for nodo, (x, y) in pos.items()}

        nx.draw_networkx_labels(
            grafo.grafo, pos_labels, labels=etiquetas_nodos, font_size=10, ax=self.axes
        )

        # Etiquetas de flujo en las aristas
        etiquetas_aristas = nx.get_edge_attributes(grafo.grafo, "capacidad_flujo")
        nx.draw_networkx_edge_labels(
            grafo.grafo, pos, edge_labels=etiquetas_aristas, ax=self.axes
        )

        # Redibujar el canvas
        self.draw()


    def _agregar_imagen(self, ruta, x, y):
        try:
            imagen = plt.imread(ruta)
            im = OffsetImage(imagen, zoom=0.1)
            ab = AnnotationBbox(im, (x, y), frameon=False)
            self.axes.add_artist(ab)
        except FileNotFoundError:
            print(f"No se encontró la imagen en {ruta}.")

        
class Interfaz(QMainWindow):
    def __init__(self):
        super().__init__()
        self.red_agua = RedDeAgua()

        # Configuración de la ventana principal
        self.setWindowTitle("Sistema de Distribución de Agua")
        self.setGeometry(100, 100, 800, 600)

        # Layout principal
        layout_principal = QVBoxLayout()

        # Layout horizontal para los botones
        layout_botones = QHBoxLayout()

        # Botones
        agregar_casa_btn = QPushButton("Agregar Casa")
        agregar_casa_btn.clicked.connect(self.agregar_casa)
        layout_botones.addWidget(agregar_casa_btn)

        agregar_tuberia_btn = QPushButton("Agregar Tubería")
        agregar_tuberia_btn.clicked.connect(self.agregar_tuberia)
        layout_botones.addWidget(agregar_tuberia_btn)

        agregar_tanque_btn = QPushButton("Agregar Tanque con Capacidad")
        agregar_tanque_btn.clicked.connect(self.agregar_tanque_con_capacidad)
        layout_botones.addWidget(agregar_tanque_btn)

        eliminar_casa_btn = QPushButton("Eliminar Casa")
        eliminar_casa_btn.clicked.connect(self.eliminar_casa)
        layout_botones.addWidget(eliminar_casa_btn)

        eliminar_tanque_btn = QPushButton("Eliminar Tanque")
        eliminar_tanque_btn.clicked.connect(self.eliminar_tanque)
        layout_botones.addWidget(eliminar_tanque_btn)

        eliminar_tuberia_btn = QPushButton("Eliminar Tubería")
        eliminar_tuberia_btn.clicked.connect(self.eliminar_tuberia)
        layout_botones.addWidget(eliminar_tuberia_btn)

        boton_obstruccion = QPushButton("Crear Obstrucción")
        boton_obstruccion.clicked.connect(self.mostrar_formulario_obstruccion)
        layout_botones.addWidget(boton_obstruccion)

        cargar_datos_btn = QPushButton("Cargar Datos")
        cargar_datos_btn.clicked.connect(self.cargar_datos_desde_archivo)
        layout_botones.addWidget(cargar_datos_btn)
        
        cambiar_sentido_btn = QPushButton("Cambiar Sentido de Tubería")
        cambiar_sentido_btn.clicked.connect(self.cambiar_sentido_tuberia)
        layout_botones.addWidget(cambiar_sentido_btn)
        
        verificar_suministro_btn = QPushButton("Verificar Suministro")
        verificar_suministro_btn.clicked.connect(self.verificar_suministro)
        layout_botones.addWidget(verificar_suministro_btn)
        
        buscar_ruta_btn = QPushButton("Buscar Ruta Alternativa")
        buscar_ruta_btn.clicked.connect(self.buscar_y_mostrar_ruta_alternativa)
        layout_botones.addWidget(buscar_ruta_btn)
        
        calcular_flujo_btn = QPushButton("Calcular Flujo Máximo")
        calcular_flujo_btn.clicked.connect(self.calcular_flujo_maximo)
        layout_botones.addWidget(calcular_flujo_btn)
        
        recargar_grafo_btn = QPushButton("Recargar Grafo")
        recargar_grafo_btn.clicked.connect(self.recargar_grafo)
        layout_botones.addWidget(recargar_grafo_btn)

        # Agregar el layout de botones al layout principal
        layout_principal.addLayout(layout_botones)

           # Widget de Matplotlib para el grafo
        self.canvas = MplCanvas(self)
        layout_principal.addWidget(self.canvas)

        # Crear un widget de texto para el log de sugerencias
        self.log_widget = QTextEdit(self)
        self.log_widget.setReadOnly(True)  # Hacer que el log sea solo lectura
        # self.log_widget.setFixedWidth(1600)  # Limitar el tamaño
        self.log_widget.setFixedHeight(100)
        layout_principal.addWidget(self.log_widget)
        
        # Widget y layout central
        central_widget = QWidget()
        central_widget.setLayout(layout_principal)
        self.setCentralWidget(central_widget)
        
    def mostrar_formulario_obstruccion(self):
        # Crear un formulario para seleccionar la tubería y el porcentaje de obstrucción
        dialog = QDialog(self)
        dialog.setWindowTitle("Crear Obstrucción")

        layout = QVBoxLayout(dialog)

        # Campos para seleccionar nodos y porcentaje de obstrucción
        combo_nodo1 = QComboBox()
        combo_nodo2 = QComboBox()

        # Rellenar nodos existentes
        combo_nodo1.addItems(self.red_agua.grafo.nodes)
        combo_nodo2.addItems(self.red_agua.grafo.nodes)

        input_obstruccion = QSpinBox()
        input_obstruccion.setRange(-1, 100)  # Rango de obstrucción (-1 para total)

        layout.addWidget(QLabel("Seleccione el nodo 1:"))
        layout.addWidget(combo_nodo1)
        layout.addWidget(QLabel("Seleccione el nodo 2:"))
        layout.addWidget(combo_nodo2)
        layout.addWidget(QLabel("Porcentaje de obstrucción (0-100, -1 para total):"))
        layout.addWidget(input_obstruccion)

        # Botón para confirmar
        boton_confirmar = QPushButton("Aplicar Obstrucción")
        boton_confirmar.clicked.connect(
            lambda: self.aplicar_obstruccion(dialog, combo_nodo1, combo_nodo2, input_obstruccion)
        )
        layout.addWidget(boton_confirmar)

        dialog.setLayout(layout)
        dialog.exec()

    def aplicar_obstruccion(self, dialog, combo_nodo1, combo_nodo2, input_obstruccion):
        nodo1 = combo_nodo1.currentText()
        nodo2 = combo_nodo2.currentText()
        obstruccion = input_obstruccion.value()

        try:
            self.red_agua.editar_tuberia(nodo1, nodo2, obstruccion)

            # Verificar si alguna casa no está siendo suplida y buscar rutas alternativas
            for casa in [nodo for nodo, data in self.red_agua.grafo.nodes(data=True) if data["tipo"] == "casa"]:
                flujo_suficiente = self.red_agua.verificar_demanda_casa(casa)
                if not flujo_suficiente:
                    ruta_alternativa, flujo = self.red_agua.buscar_ruta_alternativa(casa)
                    if ruta_alternativa:
                        self.mostrar_sugerencia(
                            f"Ruta alternativa encontrada para {casa}: {' -> '.join(ruta_alternativa)} con flujo {flujo}L/s."
                        )
                        self.canvas.dibujar_grafo(self.red_agua, ruta_alternativa)
                    else:
                        self.mostrar_sugerencia(f"No se encontró una ruta alternativa para {casa}.")
                        QMessageBox.warning(self, "Sin Rutas Alternativas", f"No se encontró una ruta para suplir {casa}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al aplicar la obstrucción: {e}")

        dialog.accept()
        
    def cambiar_sentido_tuberia(self):
        """
        Permite cambiar el sentido de una tubería.
        """
        # Pedir el nodo origen
        nodo_origen, ok1 = QInputDialog.getText(self, "Cambiar Sentido de Tubería", "Ingrese el nodo origen:")
        if not ok1 or not nodo_origen:
            self.mostrar_sugerencia("Operación cancelada o nodo origen inválido.")
            return

        # Pedir el nodo destino
        nodo_destino, ok2 = QInputDialog.getText(self, "Cambiar Sentido de Tubería", "Ingrese el nodo destino:")
        if not ok2 or not nodo_destino:
            self.mostrar_sugerencia("Operación cancelada o nodo destino inválido.")
            return
        # Llamar al backend para cambiar el sentido de la tubería
        if self.red_agua.grafo.has_edge(nodo_origen, nodo_destino):
            self.red_agua.cambiar_sentido_tuberia(nodo_origen, nodo_destino)
            self.mostrar_sugerencia(f"El sentido de la tubería {nodo_origen} -> {nodo_destino} fue cambiado exitosamente.")
            self.canvas.draw()
        else:
            self.mostrar_sugerencia(f"No existe una tubería desde {nodo_origen} a {nodo_destino}.")


    def agregar_casa(self):
        casa, ok = QInputDialog.getText(self, "Agregar Casa", "Ingrese el nombre de la casa:")
        if ok and casa:
            demanda, ok2 = QInputDialog.getInt(self, "Demanda de la Casa", "Ingrese la demanda de agua (L/s):", min=1)
            if ok2:
                self.red_agua.agregar_casa(casa, demanda)
                QMessageBox.information(self, "Éxito", f"Casa {casa} agregada con demanda {demanda} L/s.")
                self.canvas.dibujar_grafo(self.red_agua)
                
    def eliminar_casa(self):
        casa, ok = QInputDialog.getText(self, "Eliminar Casa", "Ingrese el nombre de la casa a eliminar:")
        if ok and casa:
            respuesta = QMessageBox.question(self, "Confirmar eliminación", f"¿Está seguro de que desea eliminar la casa {casa}?", 
                                            QMessageBox.Yes | QMessageBox.No)
            if respuesta == QMessageBox.Yes:
                self.red_agua.eliminar_casa(casa)
                QMessageBox.information(self, "Éxito", f"La casa {casa} ha sido eliminada.")
                self.canvas.dibujar_grafo(self.red_agua)

    def agregar_tuberia(self):
        nodo1, ok1 = QInputDialog.getText(self, "Agregar Tubería", "Ingrese el primer nodo (casa o tanque):")
        if ok1 and nodo1:
            nodo2, ok2 = QInputDialog.getText(self, "Agregar Tubería", "Ingrese el segundo nodo (casa o tanque):")
            if ok2 and nodo2:
                capacidad_flujo, ok3 = QInputDialog.getInt(self, "Capacidad de Flujo", "Ingrese la capacidad de flujo (L/s):", min=1)
                if ok3:
                    try:
                        self.red_agua.agregar_tuberia(nodo1, nodo2, capacidad_flujo)
                        QMessageBox.information(
                            self, "Éxito", f"Tubería agregada entre {nodo1} y {nodo2} con capacidad de flujo {capacidad_flujo} L/s."
                        )
                    except OverflowError as e:
                        QMessageBox.warning(self, "Desbordamiento", str(e))
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"No se pudo agregar la tubería: {e}")
                    finally:
                        self.canvas.dibujar_grafo(self.red_agua)
                    
    def eliminar_tuberia(self):
        nodo1, ok1 = QInputDialog.getText(self, "Eliminar Tubería", "Ingrese el primer nodo (casa o tanque):")
        if ok1 and nodo1:
            nodo2, ok2 = QInputDialog.getText(self, "Eliminar Tubería", "Ingrese el segundo nodo (casa o tanque):")
            if ok2 and nodo2:
                respuesta = QMessageBox.question(self, "Confirmar eliminación", f"¿Está seguro de que desea eliminar la tubería entre {nodo1} y {nodo2}?", 
                                                QMessageBox.Yes | QMessageBox.No)
                if respuesta == QMessageBox.Yes:
                    self.red_agua.eliminar_tuberia(nodo1, nodo2)
                    QMessageBox.information(self, "Éxito", f"La tubería entre {nodo1} y {nodo2} ha sido eliminada.")
                    self.canvas.dibujar_grafo(self.red_agua)
                    
    def mostrar_formulario_obstruccion(self):
        # Pedir el primer nodo
        nodo1, ok1 = QInputDialog.getText(self, "Crear Obstrucción", "Ingrese el nombre del primer nodo:")
        if not ok1 or not nodo1:
            return  # Salir si el usuario cancela o no ingresa nada

        # Pedir el segundo nodo
        nodo2, ok2 = QInputDialog.getText(self, "Crear Obstrucción", "Ingrese el nombre del segundo nodo:")
        if not ok2 or not nodo2:
            return

        # Pedir el porcentaje de obstrucción
        obstruccion, ok3 = QInputDialog.getInt(
            self, "Crear Obstrucción", 
            "Ingrese el porcentaje de obstrucción (0-100, -1 para total):",
            min=-1, max=100
        )
        if not ok3:
            return

        # Llamar al backend para aplicar la obstrucción
        try:
            self.red_agua.editar_tuberia(nodo1, nodo2, obstruccion)
            QMessageBox.information(self, "Éxito", f"Se aplicó una obstrucción del {obstruccion}% entre {nodo1} y {nodo2}.")
            self.canvas.dibujar_grafo(self.red_agua)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo aplicar la obstrucción: {e}")

    def aplicar_obstruccion(self, dialog):
        nodo1 = self.combo_nodo1.currentText()
        nodo2 = self.combo_nodo2.currentText()
        obstruccion = self.input_obstruccion.value()

        # Llamar al backend para modificar la tubería
        self.backend.editar_tuberia(nodo1, nodo2, obstruccion)
        dialog.accept()


    def agregar_tanque_con_capacidad(self):
        nombre_tanque, ok1 = QInputDialog.getText(self, "Agregar Tanque", "Ingrese el nombre del tanque:")
        if ok1 and nombre_tanque:
            capacidad, ok2 = QInputDialog.getInt(self, "Capacidad del Tanque", "Ingrese la capacidad del tanque (L):", min=1)
            if ok2:
                conexiones = []
                while True:
                    nodo, ok3 = QInputDialog.getText(self, "Agregar Conexión", "Ingrese un nodo (casa o tanque) o presione 'Cancelar' para finalizar:")
                    if not ok3:
                        break
                    conexiones.append(nodo)
                self.red_agua.agregar_tanque_con_capacidad(nombre_tanque, capacidad, conexiones)
                QMessageBox.information(self, "Éxito", f"Tanque {nombre_tanque} agregado con capacidad {capacidad} L.")
                self.canvas.dibujar_grafo(self.red_agua)
                
    def eliminar_tanque(self):
        tanque, ok = QInputDialog.getText(self, "Eliminar Tanque", "Ingrese el nombre del tanque a eliminar:")
        if ok and tanque:
            respuesta = QMessageBox.question(self, "Confirmar eliminación", f"¿Está seguro de que desea eliminar el tanque {tanque}?", 
                                            QMessageBox.Yes | QMessageBox.No)
            if respuesta == QMessageBox.Yes:
                self.red_agua.eliminar_tanque(tanque)
                QMessageBox.information(self, "Éxito", f"El tanque {tanque} ha sido eliminado.")
                self.canvas.dibujar_grafo(self.red_agua)


    def cargar_datos_desde_archivo(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo JSON", "", "Archivos JSON (*.json)")
        if archivo:
            try:
                self.red_agua.cargar_desde_json(archivo)
                QMessageBox.information(self, "Éxito", "Datos cargados exitosamente.")
                self.canvas.dibujar_grafo(self.red_agua)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos: {e}")
        
    def mostrar_sugerencia(self, sugerencia):
        """
        Muestra una sugerencia en el log.
        """
        self.log_widget.append(f"Sugerencia: {sugerencia}")
        self.log_widget.ensureCursorVisible()  # Desplazar el log hacia el final


    def verificar_suministro(self):
        """
        Llama al backend para verificar el suministro de agua y realiza la verificación de consistencia de la red.
        """
        # Verificar la consistencia de la red antes de realizar cualquier acción
        errores_red = []
        
        # Verificar conexiones duplicadas, detectar bucles, y verificar nodos no definidos
        errores_red.extend(self.red_agua.verificar_conexiones_duplicadas())
        errores_red.extend(self.red_agua.detectar_bucles())
        errores_red.extend(self.red_agua.verificar_conexiones_con_nodos_no_definidos())

        # Mostrar las sugerencias de la red (si hay errores)
        if errores_red:
            for error in errores_red:
                self.mostrar_sugerencia(error)  # Mostrar la sugerencia en la interfaz

        # Proponer nuevas conexiones para mejorar la red en caso de problemas
        sugerencias_conexiones = self.red_agua.proponer_nuevas_conexiones()  # Obtener sugerencias

        # Mostrar las sugerencias de nuevas conexiones
        for sugerencia in sugerencias_conexiones:
            self.mostrar_sugerencia(sugerencia)  # Mostrar sugerencia en la interfaz

        # Identificar casas sin servicio
        casas_sin_servicio = self.red_agua.identificar_casas_sin_servicio()

        if casas_sin_servicio:
            # Agrupar casas sin servicio y proponer nuevos tanques
            grupos_casas = self.red_agua.agrupar_casas_sin_servicio(casas_sin_servicio)
            sugerencias_tanques = self.red_agua.proponer_nuevos_tanques(grupos_casas)

            # Mostrar sugerencias de nuevos tanques
            for sugerencia in sugerencias_tanques:
                self.mostrar_sugerencia(sugerencia)  # Mostrar sugerencia en la interfaz

        # Luego se verifica el suministro
        resultados = self.red_agua.verificar_suministro()

        if not resultados:
            QMessageBox.information(self, "Suministro Completo", "Todas las casas tienen suficiente agua.")
        else:
            for casa, info in resultados.items():
                self.mostrar_sugerencia(
                    f"{casa}: {info['mensaje']} "
                    f"(Recibido: {info['flujo_recibido']}L/s, Demanda: {info['demanda']}L/s)"
                )
            QMessageBox.warning(
                self, "Problemas de Suministro", "Algunas casas no tienen suficiente agua. Revisa el log para más detalles."
            )


    def dibujar_grafo(self, grafo, ruta_alternativa=None):
        self.axes.clear()
        pos = nx.circular_layout(grafo.grafo)
        
        colores_nodos = ["blue" if data["tipo"] == "tanque" else "green" 
                        for _, data in grafo.grafo.nodes(data=True)]
        colores_aristas = ["orange" if datos.get("obstruccion", 0) > 0 else "blue"
                        for _, _, datos in grafo.grafo.edges(data=True)]
        
        # Resaltar la ruta alternativa
        if ruta_alternativa:
            for i in range(len(ruta_alternativa) - 1):
                u, v = ruta_alternativa[i], ruta_alternativa[i+1]
                if (u, v) in grafo.grafo.edges:
                    idx = list(grafo.grafo.edges).index((u, v))
                    colores_aristas[idx] = "green"
        
        nx.draw(
            grafo.grafo, pos, with_labels=True, node_color=colores_nodos, 
            edge_color=colores_aristas, node_size=600, font_weight="bold", ax=self.axes
        )
        self.draw()
        
    def buscar_y_mostrar_ruta_alternativa(self):
        for casa in [nodo for nodo, datos in self.red_agua.grafo.nodes(data=True) if datos["tipo"] == "casa"]:
            ruta_alternativa, flujo = self.red_agua.buscar_ruta_alternativa_optima(casa)
            if ruta_alternativa:
                self.mostrar_sugerencia(
                    f"Ruta alternativa encontrada para {casa}: {' -> '.join(ruta_alternativa)} con flujo {flujo} L/s."
                )
                self.canvas.dibujar_grafo(self.red_agua, ruta_alternativa)
            else:
                self.mostrar_sugerencia(f"No se encontró una ruta alternativa para {casa}.")
    
    def calcular_flujo_maximo(self):
        # Pedir el nodo fuente
        fuente, ok1 = QInputDialog.getText(self, "Nodo Fuente", "Ingrese el nombre del nodo fuente:")
        if not ok1 or not fuente:
            return

        # Pedir el nodo sumidero
        sumidero, ok2 = QInputDialog.getText(self, "Nodo Sumidero", "Ingrese el nombre del nodo sumidero:")
        if not ok2 or not sumidero:
            return
        
        # Llamar al método Ford-Fulkerson para calcular el flujo máximo
        flujo_maximo = self.red_agua.ford_fulkerson(fuente, sumidero)
        
        # Mostrar el flujo máximo calculado
        QMessageBox.information(self, "Flujo Máximo", f"El flujo máximo desde {fuente} hasta {sumidero} es: {flujo_maximo} L/s.")
        
    def recargar_grafo(self):
        try:
            # Llama al método `recargar_json` del backend
            self.red_agua.recargar_json()
            QMessageBox.information(self, "Éxito", "Grafo recargado correctamente desde el JSON.")
            
            # Redibuja el grafo para reflejar los cambios
            self.canvas.dibujar_grafo(self.red_agua)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo recargar el grafo: {e}")
            
# Correr la aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = Interfaz()
    ventana.show()
    sys.exit(app.exec_())
