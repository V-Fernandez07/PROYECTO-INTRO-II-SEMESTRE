import json
import random

# Importa los códigos de elementos y los valores predeterminados del juego.
from configuracion import (
    pincel_inicial,
    duracion_inicial,
    propagacion_inicial,
    crecimiento_inicial,
    tamano_inicial,
    elementos,
    tamano_maximo,
    tamano_minimo,
    Elemento,
)


# Tipo de dato usado para guardar una posición como (fila, columna).
Coordenada = tuple[int, int]
# Elementos que representan las tres etapas visuales de una planta.
etapas_planta = frozenset(
    {
        Elemento.planta_1,
        Elemento.planta_2,
        Elemento.planta_3,
    }
)
# Elementos que el fuego puede consumir.
combustibles = frozenset(
    {
        Elemento.pasto,
        Elemento.semilla,
        Elemento.planta_1,
        Elemento.planta_2,
        Elemento.planta_3,
    }
)
# Elementos sobre los que un animal puede apoyarse.
soportes = frozenset(
    {
        Elemento.arena,
        Elemento.piedra,
        Elemento.tierra,
        Elemento.pasto,
        Elemento.planta_1,
        Elemento.planta_2,
        Elemento.planta_3,
    }
)

# Versión del formato JSON usado al guardar mapas.
version_mapa = 1


# Guarda el estado de crecimiento y las celdas que forman una planta.
class _Planta:
    def __init__(
        self,
        celdas: list[Coordenada],
        etapa_inicial: int,
        etapa: int,
        progreso: int = 0,
    ) -> None:
        # Posiciones ocupadas por la planta, desde la base hasta la punta.
        self.celdas = celdas
        # Etapa con la que nació y etapa que ha alcanzado actualmente.
        self.etapa_inicial = etapa_inicial
        self.etapa = etapa
        # Pasos acumulados hacia la siguiente etapa de crecimiento.
        self.progreso = progreso


# Guarda el material que alimenta un fuego y cuánto tiempo le queda.
class _Fuego:
    def __init__(self, combustible: Elemento, restante: int) -> None:
        # Elemento que había en la celda antes de que se encendiera.
        self.combustible = combustible
        # Cantidad de pasos que faltan para que el fuego se apague.
        self.restante = restante


# Administra la matriz del mundo y las reglas de movimiento y crecimiento.
class Simulador:
    # Crea un mundo vacío y configura sus tamaños y ritmos de simulación.
    def __init__(
        self,
        tamano: int = tamano_inicial,
        *,
        tamano_pincel: int = pincel_inicial,
        ritmo_planta: int = crecimiento_inicial,
        ritmo_fuego: int = propagacion_inicial,
        duracion_fuego: int = duracion_inicial,
        azar: int | None = None,
    ) -> None:
        self._validar_tamano(tamano)
        self._validar_entero(tamano_pincel, "tamano_pincel")
        if tamano_pincel > tamano:
            raise ValueError("El tamano del pincel no puede superar el tamano del mundo.")
        self._validar_entero(ritmo_planta, "ticks_crecimiento_planta")
        self._validar_entero(ritmo_fuego, "ticks_propagacion_fuego")
        self._validar_entero(duracion_fuego, "ticks_duracion_fuego")

        # Configuración de tamaño y velocidad de las reglas del mundo.
        self._tamano = tamano
        self.ritmo_planta = ritmo_planta
        self.ritmo_fuego = ritmo_fuego
        self.duracion_fuego = duracion_fuego
        # Semilla y generador aleatorio para permitir resultados reproducibles.
        self._azar = azar
        self._generador_aleatorio = random.Random(azar)
        # Identificador que se asignará a la siguiente planta creada.
        self._siguiente_id_planta = 1
        self._tamano_pincel = tamano_pincel
        self._reiniciar()

    # Devuelve el número de filas y columnas del mundo.
    @property
    def tamano(self) -> int:
        return self._tamano

    # Devuelve el ancho y alto del pincel usado al dibujar.
    @property
    def tamano_pincel(self) -> int:
        return self._tamano_pincel

    # Devuelve la matriz como tuplas para que quien la consulta no la modifique.
    @property
    def matriz(self) -> tuple[tuple[int, ...], ...]:
        """Devuelve una copia de solo lectura de la matriz N por N de códigos."""
        return tuple(tuple(fila) for fila in self._matriz)

    # Devuelve cuántos pasos de simulación han transcurrido.
    @property
    def paso(self) -> int:
        return self._paso

    # Obtiene el código del elemento de una celda tras comprobar sus coordenadas.
    def celda(self, fila: int, columna: int) -> int:
        self._validar_celda(fila, columna)
        if not self._en_mundo(fila, columna):
            raise IndexError("Las coordenadas de la celda están fuera del mundo.")
        return int(self._matriz[fila][columna])

    # Cambia el tamaño del pincel y comprueba que quepa en el mundo.
    def cambiar_pincel(self, tamano_pincel: int) -> None:
        self._validar_entero(tamano_pincel, "tamano_pincel")
        if tamano_pincel > self._tamano:
            raise ValueError("El tamaño del pincel no puede superar el tamaño del mundo.")
        self._tamano_pincel = tamano_pincel

    # Dibuja un elemento con el pincel centrado en la posición indicada.
    def dibujar(self, fila: int, columna: int, elemento: int | Elemento) -> None:
        seleccionado = self._elemento(elemento)
        if seleccionado == Elemento.pasto:
            raise ValueError("El pasto se genera con agua y no se puede dibujar directamente.")
        self._validar_celda(fila, columna)

        desplazamiento = (self.tamano_pincel - 1) // 2
        primera_fila = fila - desplazamiento
        primera_columna = columna - desplazamiento
        for fila_destino in range(primera_fila, primera_fila + self.tamano_pincel):
            for columna_destino in range(primera_columna, primera_columna + self.tamano_pincel):
                if self._en_mundo(fila_destino, columna_destino):
                    self._poner((fila_destino, columna_destino), seleccionado)
        self._humedecer()
        self._apagar_fuegos()

    # Rellena el rectángulo entre dos esquinas con el elemento seleccionado.
    def rellenar(
        self,
        fila_inicial: int,
        columna_inicial: int,
        fila_final: int,
        columna_final: int,
        elemento: int | Elemento,
    ) -> None:
        seleccionado = self._elemento(elemento)
        if seleccionado == Elemento.pasto:
            raise ValueError("El pasto se genera con agua y no se puede dibujar directamente.")
        for coordenada in (fila_inicial, columna_inicial, fila_final, columna_final):
            if type(coordenada) is not int:
                raise ValueError("Las coordenadas del rectángulo deben ser enteros.")

        superior = max(0, min(fila_inicial, fila_final))
        inferior = min(self._tamano - 1, max(fila_inicial, fila_final))
        izquierda = max(0, min(columna_inicial, columna_final))
        derecha = min(self._tamano - 1, max(columna_inicial, columna_final))
        if superior > inferior or izquierda > derecha:
            return

        for fila in range(superior, inferior + 1):
            for columna in range(izquierda, derecha + 1):
                self._poner((fila, columna), seleccionado)
        self._humedecer()
        self._apagar_fuegos()

    # Ejecuta uno o varios pasos de las reglas del mundo.
    def avanzar(self, pasos: int = 1) -> None:
        if type(pasos) is not int or pasos < 0:
            raise ValueError("La cantidad de pasos debe ser un entero no negativo.")
        for _ in range(pasos):
            self._paso += 1
            self._mover_particulas()
            self._humedecer()
            self._crecer()
            self._germinar()
            self._mover_fuego()
            self._mover_animales()

    # Vacía el mundo y reinicia el generador aleatorio a su estado inicial.
    def limpiar(self) -> None:
        self._reiniciar()
        self._generador_aleatorio = random.Random(self._azar)

    # Cambia el tamaño del mundo y crea una matriz vacía con ese tamaño.
    def redimensionar(self, tamano: int) -> None:
        self._validar_tamano(tamano)
        self._tamano = tamano
        self.cambiar_pincel(min(self.tamano_pincel, tamano))
        self.limpiar()

    # Guarda la matriz, configuración y estados internos en un archivo JSON.
    def guardar(self, ruta) -> None:
        # El documento conserva claves en inglés para mantener el formato del juego.
        documento = {
            "format_version": version_mapa,
            "size": self._tamano,
            "elements": {str(codigo): nombre for codigo, nombre in elementos.items()},
            "grid": self._matriz,
            "tick": self._paso,
            "brush_size": self.tamano_pincel,
            "plant_growth_ticks": self.ritmo_planta,
            "fire_spread_ticks": self.ritmo_fuego,
            "fire_lifetime_ticks": self.duracion_fuego,
            "plants": [
                {
                    "id": id_planta,
                    "cells": [list(celda) for celda in planta.celdas],
                    "base_stage": planta.etapa_inicial,
                    "stage": planta.etapa,
                    "progress": planta.progreso,
                }
                for id_planta, planta in sorted(self._plantas.items())
            ],
            "fires": [
                {
                    "position": list(posicion),
                    "fuel": int(fuego.combustible),
                    "remaining": fuego.restante,
                }
                for posicion, fuego in sorted(self._fuegos.items())
            ],
        }
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(documento, archivo, indent=2, ensure_ascii=False)
            archivo.write("\n")

    # Lee un archivo JSON, valida sus datos y restaura el estado del mundo.
    def cargar(self, ruta) -> None:
        with open(ruta, "r", encoding="utf-8") as archivo:
            documento = json.load(archivo)
        estado = self._leer_mapa(documento)

        self._tamano = estado["tamano"]
        self._matriz = estado["matriz"]
        self._paso = estado["paso"]
        self.cambiar_pincel(estado["tamano_pincel"])
        self.ritmo_planta = estado["ticks_crecimiento_planta"]
        self.ritmo_fuego = estado["ticks_propagacion_fuego"]
        self.duracion_fuego = estado["ticks_duracion_fuego"]
        self._plantas = estado["plantas"]
        self._fuegos = estado["fuegos"]
        self._planta_en = estado["planta_en"]
        self._siguiente_id_planta = max(self._plantas, default=0) + 1

    # Inicializa una matriz de aire y elimina todos los estados de la partida.
    def _reiniciar(self) -> None:
        # Matriz cuadrada donde cada número representa un Elemento.
        self._matriz = [
            [Elemento.aire.value for _ in range(self._tamano)]
            for _ in range(self._tamano)
        ]
        # Paso actual, plantas, fuegos y relación entre celdas y plantas.
        self._paso = 0
        self._plantas: dict[int, _Planta] = {}
        self._planta_en: dict[Coordenada, int] = {}
        self._fuegos: dict[Coordenada, _Fuego] = {}
        self._siguiente_id_planta = 1

    # Coloca un elemento en una celda y actualiza sus datos asociados.
    def _poner(self, posicion: Coordenada, elemento: Elemento) -> None:
        elemento_anterior = Elemento(self._matriz[posicion[0]][posicion[1]])
        if elemento == Elemento.fuego:
            self._encender(posicion)
            return
        if elemento_anterior == Elemento.fuego and elemento == Elemento.agua:
            self._apagar(posicion)

        self._quitar_estado(posicion)
        if elemento in etapas_planta:
            etapa = int(elemento) - int(Elemento.planta_1) + 1
            id_planta = self._siguiente_id_planta
            self._siguiente_id_planta += 1
            self._plantas[id_planta] = _Planta([posicion], etapa, etapa)
            self._planta_en[posicion] = id_planta
        self._matriz[posicion[0]][posicion[1]] = int(elemento)

    # Elimina de una celda cualquier información de fuego o planta.
    def _quitar_estado(self, posicion: Coordenada) -> None:
        self._fuegos.pop(posicion, None)
        id_planta = self._planta_en.get(posicion)
        if id_planta is not None:
            self._quitar_planta(id_planta)

    # Borra una planta completa y devuelve las posiciones que ocupaba.
    def _quitar_planta(self, id_planta: int) -> list[Coordenada]:
        planta = self._plantas.pop(id_planta)
        for posicion in planta.celdas:
            self._planta_en.pop(posicion, None)
            fila, columna = posicion
            if Elemento(self._matriz[fila][columna]) in etapas_planta:
                self._matriz[fila][columna] = Elemento.aire.value
        return planta.celdas

    # Enciende una celda, guarda su combustible y retira el estado de planta.
    def _encender(self, posicion: Coordenada) -> None:
        fila, columna = posicion
        elemento_anterior = Elemento(self._matriz[fila][columna])
        if elemento_anterior == Elemento.agua:
            return
        if elemento_anterior == Elemento.fuego:
            fuego = self._fuegos[posicion]
            fuego.restante = self.duracion_fuego
            return

        celdas_planta: list[Coordenada] = []
        id_planta = self._planta_en.get(posicion)
        if id_planta is not None:
            celdas_planta = self._quitar_planta(id_planta)
            for celda in celdas_planta:
                if celda != posicion:
                    self._matriz[celda[0]][celda[1]] = Elemento.tierra.value

        self._fuegos[posicion] = _Fuego(elemento_anterior, self.duracion_fuego)
        self._matriz[fila][columna] = Elemento.fuego.value

    # Apaga el fuego de una celda y deja el resultado de quemar su combustible.
    def _apagar(self, posicion: Coordenada) -> None:
        fuego = self._fuegos.pop(posicion, None)
        if fuego is None:
            return
        fila, columna = posicion
        self._matriz[fila][columna] = self._quemado(fuego.combustible).value

    # Determina en qué elemento se transforma cada material al quemarse.
    @staticmethod
    def _quemado(combustible: Elemento) -> Elemento:
        if combustible in etapas_planta or combustible == Elemento.pasto:
            return Elemento.tierra
        if combustible == Elemento.semilla:
            return Elemento.aire
        return combustible

    # Convierte en pasto la tierra que tiene agua en una celda vecina.
    def _humedecer(self) -> None:
        hidratadas: set[Coordenada] = set()
        for fila in range(self._tamano):
            for columna in range(self._tamano):
                if self._matriz[fila][columna] != Elemento.agua.value:
                    continue
                for vecina in self._adyacentes((fila, columna)):
                    if self._matriz[vecina[0]][vecina[1]] == Elemento.tierra.value:
                        hidratadas.add(vecina)
        for fila, columna in hidratadas:
            self._matriz[fila][columna] = Elemento.pasto.value

    # Apaga los fuegos que están junto al agua.
    def _apagar_fuegos(self) -> None:
        fuegos_mojados = []
        for posicion in self._fuegos:
            if any(
                self._matriz[fila][columna] == Elemento.agua.value
                for fila, columna in self._adyacentes(posicion)
            ):
                fuegos_mojados.append(posicion)
        for posicion in fuegos_mojados:
            self._apagar(posicion)

    # Mueve arena, agua y semillas hacia abajo y, si hace falta, hacia los lados.
    def _mover_particulas(self) -> None:
        columnas = list(range(self._tamano))
        movidos_en_este_paso: set[Coordenada] = set()
        for fila in range(self._tamano - 1, -1, -1):
            self._generador_aleatorio.shuffle(columnas)
            for columna in columnas:
                posicion = (fila, columna)
                if posicion in movidos_en_este_paso:
                    continue
                elemento = Elemento(self._matriz[fila][columna])
                if elemento not in (Elemento.arena, Elemento.agua, Elemento.semilla):
                    continue
                debajo = (fila + 1, columna)
                if fila + 1 < self._tamano and self._vacia(debajo):
                    self._mover(posicion, debajo)
                    movidos_en_este_paso.add(debajo)
                    continue
                if elemento == Elemento.semilla:
                    continue
                diagonales = [(fila + 1, columna - 1), (fila + 1, columna + 1)]
                self._generador_aleatorio.shuffle(diagonales)
                movido = False
                for destino in diagonales:
                    if self._en_mundo(*destino) and self._vacia(destino):
                        self._mover(posicion, destino)
                        movidos_en_este_paso.add(destino)
                        movido = True
                        break
                if movido or elemento == Elemento.arena:
                    continue
                laterales = [(fila, columna - 1), (fila, columna + 1)]
                self._generador_aleatorio.shuffle(laterales)
                for destino in laterales:
                    if self._en_mundo(*destino) and self._vacia(destino):
                        self._mover(posicion, destino)
                        movidos_en_este_paso.add(destino)
                        break

    # Traslada el contenido de una celda a otra y deja aire en el origen.
    def _mover(self, origen: Coordenada, destino: Coordenada) -> None:
        fila_origen, columna_origen = origen
        fila_destino, columna_destino = destino
        self._matriz[fila_destino][columna_destino] = self._matriz[fila_origen][columna_origen]
        self._matriz[fila_origen][columna_origen] = Elemento.aire.value

    # Germina semillas que han caído encima de una celda de pasto.
    def _germinar(self) -> None:
        semillas = [
            (fila, columna)
            for fila in range(self._tamano - 1)
            for columna in range(self._tamano)
            if self._matriz[fila][columna] == Elemento.semilla.value
            and self._matriz[fila + 1][columna] == Elemento.pasto.value
        ]
        for posicion in semillas:
            self._plantar(posicion, 1)

    # Crea una planta de la etapa indicada y registra su posición.
    def _plantar(self, posicion: Coordenada, etapa: int) -> None:
        id_planta = self._siguiente_id_planta
        self._siguiente_id_planta += 1
        self._plantas[id_planta] = _Planta([posicion], etapa, etapa)
        self._planta_en[posicion] = id_planta
        self._matriz[posicion[0]][posicion[1]] = (
            int(Elemento.planta_1) + etapa - 1
        )

    # Hace crecer cada planta una etapa cuando ha acumulado suficientes pasos.
    def _crecer(self) -> None:
        for id_planta in tuple(self._plantas):
            planta = self._plantas.get(id_planta)
            if planta is None or planta.etapa >= 3:
                continue
            planta.progreso += 1
            if planta.progreso < self.ritmo_planta:
                continue

            fila, columna = planta.celdas[0]
            planta.etapa += 1
            planta.progreso = 0
            self._matriz[fila][columna] = (
                int(Elemento.planta_1) + planta.etapa - 1
            )

    # Reduce la duración de los fuegos, los apaga o intenta propagarlos.
    def _mover_fuego(self) -> None:
        fuegos_actuales = tuple(self._fuegos)
        for posicion in fuegos_actuales:
            fuego = self._fuegos.get(posicion)
            if fuego is None:
                continue
            if any(
                self._matriz[fila][columna] == Elemento.agua.value
                for fila, columna in self._adyacentes(posicion)
            ):
                self._apagar(posicion)
                continue

            fuego.restante -= 1
            if fuego.restante <= 0:
                self._apagar(posicion)
                continue
            if self._paso % self.ritmo_fuego == 0:
                self._propagar(posicion)

    # Enciende al azar una celda combustible vecina al fuego.
    def _propagar(self, posicion: Coordenada) -> None:
        candidatos = [
            vecina
            for vecina in self._adyacentes(posicion)
            if Elemento(self._matriz[vecina[0]][vecina[1]])
            in combustibles
        ]
        if candidatos:
            self._encender(self._generador_aleatorio.choice(candidatos))

    # Deja caer a los animales y los mueve a la derecha cuando tienen apoyo.
    def _mover_animales(self) -> None:
        animales = [
            (fila, columna)
            for fila in range(self._tamano)
            for columna in range(self._tamano)
            if self._matriz[fila][columna] == Elemento.animal.value
        ]
        for fila, columna in sorted(animales, key=lambda celda: (celda[0], -celda[1])):
            if self._matriz[fila][columna] != Elemento.animal.value:
                continue
            if any(
                self._matriz[vecina[0]][vecina[1]] == Elemento.fuego.value
                for vecina in self._adyacentes((fila, columna))
            ):
                self._matriz[fila][columna] = Elemento.aire.value
                continue

            debajo = (fila + 1, columna)
            if fila + 1 < self._tamano and self._matriz[debajo[0]][debajo[1]] == Elemento.fuego.value:
                self._matriz[fila][columna] = Elemento.aire.value
                continue
            if fila + 1 < self._tamano and self._vacia(debajo):
                self._mover((fila, columna), debajo)
                continue
            if not self._apoyado(fila, columna):
                continue

            destino = (fila, columna + 1)
            if not self._en_mundo(*destino) or not self._apoyado(*destino):
                continue

            elemento_destino = Elemento(self._matriz[destino[0]][destino[1]])
            if elemento_destino == Elemento.agua or elemento_destino == Elemento.fuego:
                continue
            if elemento_destino in etapas_planta:
                id_planta = self._planta_en.get(destino)
                if id_planta is not None:
                    self._quitar_planta(id_planta)
            elif elemento_destino == Elemento.pasto:
                self._matriz[destino[0]][destino[1]] = Elemento.aire.value

            if self._vacia(destino):
                self._mover((fila, columna), destino)

    # Comprueba si una celda tiene suelo u otro material que sostenga al animal.
    def _apoyado(self, fila: int, columna: int) -> bool:
        if fila == self._tamano - 1:
            return True
        debajo = Elemento(self._matriz[fila + 1][columna])
        return debajo in soportes

    # Devuelve las celdas vecinas arriba, abajo, a la izquierda y a la derecha.
    def _adyacentes(self, posicion: Coordenada) -> list[Coordenada]:
        fila, columna = posicion
        return [
            (fila_vecina, columna_vecina)
            for fila_vecina, columna_vecina in (
                (fila - 1, columna),
                (fila + 1, columna),
                (fila, columna - 1),
                (fila, columna + 1),
            )
            if self._en_mundo(fila_vecina, columna_vecina)
        ]

    # Indica si la celda contiene aire y por lo tanto está libre.
    def _vacia(self, posicion: Coordenada) -> bool:
        return self._matriz[posicion[0]][posicion[1]] == Elemento.aire.value

    # Comprueba que una fila y columna estén dentro de los límites del mundo.
    def _en_mundo(self, fila: int, columna: int) -> bool:
        return 0 <= fila < self._tamano and 0 <= columna < self._tamano

    # Rechaza coordenadas que no sean números enteros.
    def _validar_celda(self, fila: int, columna: int) -> None:
        if type(fila) is not int or type(columna) is not int:
            raise ValueError("Las coordenadas de las celdas deben ser enteros.")

    # Valida que un ajuste expresado como cantidad sea un entero positivo.
    @staticmethod
    def _validar_entero(valor: int, nombre: str) -> None:
        if type(valor) is not int or valor < 1:
            raise ValueError(f"{nombre} debe ser un entero positivo.")

    # Comprueba que el tamaño del mundo esté dentro de los límites permitidos.
    @staticmethod
    def _validar_tamano(tamano: int) -> None:
        if type(tamano) is not int or not tamano_minimo <= tamano <= tamano_maximo:
            raise ValueError(
                f"El tamano del mundo debe ser un entero entre "
                f"{tamano_minimo} y {tamano_maximo}."
            )

    # Convierte un código numérico en Elemento o informa que no es válido.
    @staticmethod
    def _elemento(elemento: int | Elemento) -> Elemento:
        if type(elemento) is not int and not isinstance(elemento, Elemento):
            raise ValueError("El codigo del elemento debe ser un entero valido.")
        try:
            return Elemento(elemento)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Codigo de elemento desconocido: {elemento!r}.") from error

    # Valida el contenido completo del mapa y devuelve el estado listo para cargar.
    @staticmethod
    def _leer_mapa(documento: object) -> dict:
        if not isinstance(documento, dict):
            raise ValueError("El mapa debe contener un objeto JSON.")
        if (
            type(documento.get("format_version")) is not int
            or documento.get("format_version") != version_mapa
        ):
            raise ValueError("La version del formato del mapa no existe o no es compatible.")

        # Comprueba que los nombres de elementos coincidan con esta versión.
        nombres_esperados = {str(codigo): nombre for codigo, nombre in elementos.items()}
        if documento.get("elements") != nombres_esperados:
            raise ValueError("Los codigos de elementos del mapa no corresponden a este juego.")

        tamano = documento.get("size")
        Simulador._validar_tamano(tamano)
        matriz_cruda = documento.get("grid")
        if not isinstance(matriz_cruda, list) or len(matriz_cruda) != tamano:
            raise ValueError("La matriz del mapa debe tener exactamente N filas.")

        # Comprueba que la matriz tenga el tamaño correcto y códigos conocidos.
        matriz: list[list[int]] = []
        for fila in matriz_cruda:
            if not isinstance(fila, list) or len(fila) != tamano:
                raise ValueError("Cada fila de la matriz debe tener exactamente N celdas.")
            fila_validada = []
            for codigo in fila:
                if type(codigo) is not int:
                    raise ValueError("Los codigos de elementos de la matriz deben ser enteros.")
                try:
                    Elemento(codigo)
                except ValueError as error:
                    raise ValueError(f"Codigo de elemento desconocido en la matriz: {codigo}.") from error
                fila_validada.append(codigo)
            matriz.append(fila_validada)

        paso = documento.get("tick")
        if type(paso) is not int or paso < 0:
            raise ValueError("El paso del mapa debe ser un entero no negativo.")
        tamano_pincel = documento.get("brush_size")
        Simulador._validar_entero(tamano_pincel, "tamano_pincel")
        if tamano_pincel > tamano:
            raise ValueError("El tamano del pincel del mapa no puede superar el del mundo.")
        ticks_crecimiento = documento.get("plant_growth_ticks")
        ticks_propagacion = documento.get("fire_spread_ticks")
        ticks_duracion = documento.get("fire_lifetime_ticks")
        Simulador._validar_entero(ticks_crecimiento, "ticks_crecimiento_planta")
        Simulador._validar_entero(ticks_propagacion, "ticks_propagacion_fuego")
        Simulador._validar_entero(ticks_duracion, "ticks_duracion_fuego")

        # Reconstruye las plantas y verifica que coincidan con las celdas del mapa.
        plantas: dict[int, _Planta] = {}
        planta_en: dict[Coordenada, int] = {}
        plantas_crudas = documento.get("plants")
        if not isinstance(plantas_crudas, list):
            raise ValueError("Los datos de las plantas del mapa deben ser una lista.")
        for registro in plantas_crudas:
            if not isinstance(registro, dict):
                raise ValueError("Cada registro de planta debe ser un objeto.")
            id_planta = registro.get("id")
            if type(id_planta) is not int or id_planta < 1 or id_planta in plantas:
                raise ValueError("Los identificadores de plantas deben ser enteros positivos unicos.")
            etapa_inicial = registro.get("base_stage")
            etapa = registro.get("stage")
            progreso = registro.get("progress")
            if (
                type(etapa_inicial) is not int
                or type(etapa) is not int
                or not 1 <= etapa_inicial <= etapa <= 3
            ):
                raise ValueError("Las etapas de las plantas deben estar entre 1 y 3.")
            if type(progreso) is not int or not 0 <= progreso < ticks_crecimiento:
                raise ValueError("El progreso de crecimiento de la planta no es valido.")
            celdas_crudas = registro.get("cells")
            if (
                not isinstance(celdas_crudas, list)
                or len(celdas_crudas) != 1
            ):
                raise ValueError("Las celdas de la planta no corresponden con la etapa guardada.")

            celdas = [
                Simulador._leer_posicion(celda_cruda, tamano) for celda_cruda in celdas_crudas
            ]
            posicion = celdas[0]
            fila, columna = posicion
            codigo_esperado = int(Elemento.planta_1) + etapa - 1
            if matriz[fila][columna] != codigo_esperado:
                raise ValueError("Los datos de la planta no corresponden con la matriz del mapa.")
            if posicion in planta_en:
                raise ValueError("Una celda no puede pertenecer a dos plantas.")
            planta_en[posicion] = id_planta
            plantas[id_planta] = _Planta(celdas, etapa_inicial, etapa, progreso)

        celdas_planta_matriz = {
            (fila, columna)
            for fila in range(tamano)
            for columna in range(tamano)
            if Elemento(matriz[fila][columna]) in etapas_planta
        }
        if celdas_planta_matriz != set(planta_en):
            raise ValueError("Cada celda de planta debe tener sus datos correspondientes.")

        # Reconstruye los fuegos y valida su combustible y duración restante.
        fuegos: dict[Coordenada, _Fuego] = {}
        fuegos_crudos = documento.get("fires")
        if not isinstance(fuegos_crudos, list):
            raise ValueError("Los datos de los fuegos del mapa deben ser una lista.")
        for registro in fuegos_crudos:
            if not isinstance(registro, dict):
                raise ValueError("Cada registro de fuego debe ser un objeto.")
            posicion = Simulador._leer_posicion(registro.get("position"), tamano)
            codigo_combustible = registro.get("fuel")
            restante = registro.get("remaining")
            if type(codigo_combustible) is not int or type(restante) is not int:
                raise ValueError(
                    "El combustible y el tiempo restante del fuego deben ser enteros."
                )
            try:
                combustible = Elemento(codigo_combustible)
            except ValueError as error:
                raise ValueError(f"Codigo de combustible desconocido: {codigo_combustible}.") from error
            if combustible == Elemento.fuego:
                raise ValueError("Una celda de fuego no puede ser su propio combustible.")
            if not 1 <= restante <= ticks_duracion:
                raise ValueError("El tiempo restante del fuego no es valido.")
            if posicion in fuegos or matriz[posicion[0]][posicion[1]] != Elemento.fuego.value:
                raise ValueError(
                    "Los datos del fuego no corresponden con la matriz del mapa."
                )
            fuegos[posicion] = _Fuego(combustible, restante)

        celdas_fuego_matriz = {
            (fila, columna)
            for fila in range(tamano)
            for columna in range(tamano)
            if matriz[fila][columna] == Elemento.fuego.value
        }
        if celdas_fuego_matriz != set(fuegos):
            raise ValueError("Cada celda de fuego debe tener sus datos correspondientes.")

        return {
            "tamano": tamano,
            "matriz": matriz,
            "paso": paso,
            "tamano_pincel": tamano_pincel,
            "ticks_crecimiento_planta": ticks_crecimiento,
            "ticks_propagacion_fuego": ticks_propagacion,
            "ticks_duracion_fuego": ticks_duracion,
            "plantas": plantas,
            "planta_en": planta_en,
            "fuegos": fuegos,
        }

    # Comprueba que una posición guardada sea una pareja de coordenadas válida.
    @staticmethod
    def _leer_posicion(valor: object, tamano: int) -> Coordenada:
        if (
            not isinstance(valor, list)
            or len(valor) != 2
            or type(valor[0]) is not int
            or type(valor[1]) is not int
            or not (0 <= valor[0] < tamano and 0 <= valor[1] < tamano)
        ):
            raise ValueError("El mapa contiene una posicion de celda no valida.")
        return valor[0], valor[1]
