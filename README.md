# Motor del juego sandbox

La lógica está separada de la interfaz y se encuentra en `simulador.py`. La configuración y los códigos de elementos están en `configuracion.py`. La interfaz puede consultar la matriz, pero debe cambiar el mundo mediante los métodos de `Simulador`.

```python
from configuracion import Elemento
from simulador import Simulador

mundo = Simulador(tamano=40)
mundo.cambiar_pincel(3)
mundo.dibujar(10, 12, Elemento.piedra)
mundo.avanzar()  # Llamar periódicamente desde la interfaz.
codigo = mundo.celda(10, 12)
```

## Métodos para la interfaz

- `Simulador(tamano=40, tamano_pincel=1, ...)`: crea una matriz cuadrada de
  tamaño entre 20 y 100.
- `mundo.matriz`, `mundo.tamano`, `mundo.paso` y `mundo.celda(fila, columna)`:
  consultan el estado. `matriz` es una
  copia de solo lectura.
- `mundo.dibujar(fila, columna, elemento)`: aplica el pincel cuadrado y recorta
  la zona en los bordes. `Elemento.aire` funciona como borrador; el pasto no
  se puede colocar directamente.
- `mundo.cambiar_pincel(celdas)`: ajusta el pincel cuadrado.
- `mundo.rellenar(fila1, columna1, fila2, columna2, elemento)`: llena
  un rectángulo inclusivo, incluso si las esquinas están invertidas.
- `mundo.avanzar(pasos=1)`: avanza la simulación.
- `mundo.redimensionar(n)`: cambia el tamaño y reinicia el mundo.
- `mundo.limpiar()`: convierte toda la matriz en aire y reinicia los estados.
- `mundo.guardar(ruta)` y `mundo.cargar(ruta)`: guardan o cargan el
  mapa. La carga valida todo antes de reemplazar el estado. Lanza `ValueError`
  si el mapa es inválido y propaga `OSError` si falla el acceso al archivo; la
  interfaz debe capturar esos errores y mostrarlos sin cerrarse.

## Reglas

Los códigos están definidos en `configuracion.py` como `Elemento.aire`,
`Elemento.arena`, `Elemento.agua`, etc.: aire (0), arena (1), agua
(2), piedra (3), tierra (4), fuego (5), semilla (6), pasto (7), etapas de planta
(8, 9 y 10) y animal terrestre (11). El pasto se genera cuando el agua toca la
tierra. Las semillas germinan sobre pasto; las plantas crecen gradualmente
hacia arriba, en tres etapas, y se detienen si no hay espacio. El animal se
mueve hacia la derecha, cae si no tiene soporte y evita el agua y los
obstáculos.

La arena y las semillas caen por gravedad. El agua cae, se desplaza en diagonal
y fluye lateralmente. El fuego se propaga sobre pasto, semillas y plantas,
desaparece al agotarse o tocar agua, y convierte el pasto quemado en tierra.
Piedra y tierra permanecen fijas. Para avanzar estas reglas, la interfaz debe
llamar a `mundo.avanzar`.

## Formato de mapas

Los mapas se guardan como JSON legible. Las claves de ese formato (por ejemplo,
`size`, `grid`, `plants` y `fires`) se mantienen en inglés; los nombres de los
elementos se guardan en español. También se guardan las etapas y el progreso de
las plantas, el estado del fuego y los parámetros necesarios para reanudar la
simulación. El cargador requiere los nombres actuales en español.

## Pruebas

Desde la carpeta del proyecto, ejecuta:

```text
python -m unittest -v
```

Las pruebas se encuentran en `test_simulador.py`, si está presente en el
proyecto.
