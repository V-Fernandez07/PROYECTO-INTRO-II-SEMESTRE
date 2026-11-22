from enum import IntEnum

# Códigos numéricos de los elementos que pueden ocupar una celda del mundo.
class Elemento(IntEnum):
    # La celda está vacía.
    aire = 0
    # Materiales y elementos básicos del entorno.
    arena = 1
    agua = 2
    piedra = 3
    tierra = 4
    fuego = 5
    # La semilla y las etapas de planta se usan durante el crecimiento.
    semilla = 6
    pasto = 7
    planta_1 = 8
    planta_2 = 9
    planta_3 = 10
    # Animal terrestre que puede desplazarse por el mundo.
    animal = 11


# Nombres que se muestran para cada código de Elemento.
elementos = {
    Elemento.aire.value: "Aire",
    Elemento.arena.value: "Arena",
    Elemento.agua.value: "Agua",
    Elemento.piedra.value: "Piedra",
    Elemento.tierra.value: "Tierra",
    Elemento.fuego.value: "Fuego",
    Elemento.semilla.value: "Semilla",
    Elemento.pasto.value: "Pasto",
    Elemento.planta_1.value: "Planta, etapa 1",
    Elemento.planta_2.value: "Planta, etapa 2",
    Elemento.planta_3.value: "Planta, etapa 3",
    Elemento.animal.value: "Animal terrestre",
}

# Límites de tamaño permitidos para la matriz cuadrada del mundo.
tamano_minimo = 20
tamano_maximo = 100
# Valores predeterminados que usa el simulador al iniciar.
tamano_inicial = 40
pincel_inicial = 1
crecimiento_inicial = 8
propagacion_inicial = 2
duracion_inicial = 6
