import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from simulador import Simulador
from configuracion import Elemento

ANCHO_MUNDO = 600
ALTO_MUNDO = 600
RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_RECURSOS = os.path.join(RUTA_BASE, 'recursos')

simulador = Simulador()
elemento_seleccionado = Elemento.arena
simulacion_pausada = False
modo_rectangulo = False
primera_esquina = None
tamano_celda = ANCHO_MUNDO / simulador.tamano
imagenes_originales = {}
imagenes_tk = {}
casillas = []
valores_visibles = []

archivos = {
    Elemento.arena: ('texturas', 'arena.png'),
    Elemento.agua: ('texturas', 'agua.png'),
    Elemento.piedra: ('texturas', 'piedra.png'),
    Elemento.tierra: ('texturas', 'tierra.png'),
    Elemento.fuego: ('efectos', 'fuego.png'),
    Elemento.semilla: ('plantas', 'semilla.png'),
    Elemento.pasto: ('texturas', 'pasto.png'),
    Elemento.planta_1: ('plantas', 'planta_1.png'),
    Elemento.planta_2: ('plantas', 'planta_2.png'),
    Elemento.planta_3: ('plantas', 'planta_3.png'),
    Elemento.animal: ('animales', 'conejo.png')
}


def cargar_png(carpeta, nombre):
    """Abre una imagen PNG conservando su transparencia."""
    ruta = os.path.join(RUTA_RECURSOS, carpeta, nombre)
    return Image.open(ruta).convert('RGBA')


def preparar_imagenes():
    """Prepara las imágenes del mundo para el tamaño actual de la matriz."""
    imagenes_tk.clear()
    lado = max(1, round(tamano_celda))
    for elemento, (carpeta, nombre) in archivos.items():
        if elemento not in imagenes_originales:
            imagenes_originales[elemento] = cargar_png(carpeta, nombre)
        imagen = imagenes_originales[elemento].resize((lado, lado), Image.Resampling.NEAREST)
        imagenes_tk[elemento] = ImageTk.PhotoImage(imagen)

    cielo = cargar_png('fondos', 'cielo.png').resize((ANCHO_MUNDO, ALTO_MUNDO), Image.Resampling.NEAREST)
    imagenes_tk['cielo'] = ImageTk.PhotoImage(cielo)

    montanas = cargar_png('fondos', 'montanas_1.png')
    montanas.thumbnail((ANCHO_MUNDO, 290), Image.Resampling.NEAREST)
    imagenes_tk['montanas'] = ImageTk.PhotoImage(montanas)


def reconstruir_lienzo():
    """Crea el fondo y las casillas que se actualizarán durante la simulación."""
    global casillas, valores_visibles
    lienzo.delete('all')
    lienzo.create_image(0, 0, image=imagenes_tk['cielo'], anchor='nw')
    lienzo.create_image(ANCHO_MUNDO // 2, ALTO_MUNDO, image=imagenes_tk['montanas'], anchor='s')
    casillas = []
    valores_visibles = []
    for fila in range(simulador.tamano):
        fila_casillas = []
        fila_valores = []
        for columna in range(simulador.tamano):
            x = (columna + 0.5) * tamano_celda
            y = (fila + 0.5) * tamano_celda
            identificador = lienzo.create_image(x, y, state='hidden')
            fila_casillas.append(identificador)
            fila_valores.append(None)
        casillas.append(fila_casillas)
        valores_visibles.append(fila_valores)
    dibujar_mundo()


def dibujar_mundo():
    """Actualiza únicamente las casillas cuyo elemento haya cambiado."""
    matriz = simulador.matriz
    for fila in range(simulador.tamano):
        for columna in range(simulador.tamano):
            elemento = matriz[fila][columna]
            if valores_visibles[fila][columna] == elemento:
                continue
            identificador = casillas[fila][columna]
            if elemento == Elemento.aire:
                lienzo.itemconfigure(identificador, state='hidden')
            else:
                lienzo.itemconfigure(identificador, image=imagenes_tk[elemento], state='normal')
            valores_visibles[fila][columna] = elemento


def seleccionar_elemento(elemento):
    """Selecciona la herramienta y resalta su icono."""
    global elemento_seleccionado
    elemento_seleccionado = elemento
    for tipo, etiqueta in botones_elementos.items():
        etiqueta.configure(bg='#ffe09b' if tipo == elemento else '#e8dfce')
    etiqueta_seleccion.configure(text='Herramienta: ' + nombres[elemento])


def coordenadas_validas(evento):
    """Convierte la posición del mouse a fila y columna de la matriz."""
    fila = int(evento.y // tamano_celda)
    columna = int(evento.x // tamano_celda)
    if 0 <= fila < simulador.tamano and 0 <= columna < simulador.tamano:
        return fila, columna
    return None


def pintar(evento):
    """Dibuja con el pincel o marca las esquinas de un rectángulo."""
    global primera_esquina
    posicion = coordenadas_validas(evento)
    if posicion is None:
        return
    fila, columna = posicion
    if modo_rectangulo:
        if primera_esquina is None:
            primera_esquina = (fila, columna)
            etiqueta_estado.configure(text='Elegí la segunda esquina')
        else:
            fila_inicial, columna_inicial = primera_esquina
            simulador.rellenar(fila_inicial, columna_inicial, fila, columna, elemento_seleccionado)
            primera_esquina = None
            etiqueta_estado.configure(text='Rectángulo aplicado')
    else:
        simulador.dibujar(fila, columna, elemento_seleccionado)
    dibujar_mundo()


def pintar_arrastrando(evento):
    """Permite dibujar mientras se mantiene presionado el mouse."""
    if not modo_rectangulo:
        pintar(evento)


def actualizar_mundo():
    """Avanza la simulación y actualiza los elementos visibles."""
    if not simulacion_pausada:
        simulador.avanzar()
        dibujar_mundo()
    ventana.after(100, actualizar_mundo)


def cambiar_tamano_pincel(valor):
    """Cambia el tamaño del pincel del simulador."""
    simulador.cambiar_pincel(int(float(valor)))


def pausar_continuar():
    """Pausa o reanuda la simulación."""
    global simulacion_pausada
    simulacion_pausada = not simulacion_pausada
    boton_pausa.configure(text='▶ Continuar' if simulacion_pausada else '⏸ Pausar')


def activar_rectangulo():
    """Activa o desactiva el modo de relleno rectangular."""
    global modo_rectangulo, primera_esquina
    modo_rectangulo = not modo_rectangulo
    primera_esquina = None
    boton_rectangulo.configure(text='▣ Rectángulo: ON' if modo_rectangulo else '▣ Rectángulo: OFF')
    etiqueta_estado.configure(text='Seleccioná dos esquinas' if modo_rectangulo else 'Pincel libre')


def limpiar_mundo():
    """Limpia la matriz y actualiza el mundo."""
    global primera_esquina
    simulador.limpiar()
    primera_esquina = None
    dibujar_mundo()


def cambiar_tamano_matriz():
    """Redimensiona la matriz y reconstruye las casillas gráficas."""
    global tamano_celda, primera_esquina
    try:
        simulador.redimensionar(int(escala_matriz.get()))
        tamano_celda = ANCHO_MUNDO / simulador.tamano
        primera_esquina = None
        preparar_imagenes()
        reconstruir_lienzo()
    except Exception as error:
        messagebox.showerror('Error al cambiar tamaño', str(error))


def guardar_mundo():
    """Guarda la simulación mediante el método del simulador."""
    ruta = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Archivos JSON', '*.json')])
    if ruta:
        try:
            simulador.guardar(ruta)
        except Exception as error:
            messagebox.showerror('Error al guardar', str(error))


def cargar_mundo():
    """Carga un mundo y muestra un error si el archivo no es válido."""
    global tamano_celda, primera_esquina
    ruta = filedialog.askopenfilename(filetypes=[('Archivos JSON', '*.json')])
    if ruta:
        try:
            simulador.cargar(ruta)
            tamano_celda = ANCHO_MUNDO / simulador.tamano
            primera_esquina = None
            escala_matriz.set(simulador.tamano)
            preparar_imagenes()
            reconstruir_lienzo()
        except Exception as error:
            messagebox.showerror('No se pudo cargar el mundo', str(error))


nombres = {
    Elemento.arena: 'Arena', Elemento.agua: 'Agua', Elemento.piedra: 'Piedra',
    Elemento.tierra: 'Tierra', Elemento.fuego: 'Fuego', Elemento.semilla: 'Semilla',
    Elemento.animal: 'Animal', Elemento.aire: 'Borrador'
}

ventana = tk.Tk()
ventana.title('Sandbox de Elementos - Pixel Art')
ventana.geometry('1050x760')
ventana.configure(bg='#d6e9d1')

try:
    preparar_imagenes()
except (OSError, FileNotFoundError) as error:
    messagebox.showerror('Faltan recursos gráficos', 'Revisá la carpeta recursos.\n\n' + str(error))
    ventana.destroy()
    raise SystemExit

marco_principal = tk.Frame(ventana, bg='#d6e9d1')
marco_principal.pack(padx=12, pady=12, fill='both', expand=True)

lienzo = tk.Canvas(marco_principal, width=ANCHO_MUNDO, height=ALTO_MUNDO, bg='#8fd4ed', highlightthickness=4, highlightbackground='#5c8062')
lienzo.pack(side='left', padx=(0, 16), anchor='n')

panel = tk.Frame(marco_principal, bg='#f8f0dd', padx=14, pady=10, relief='ridge', bd=3)
panel.pack(side='left', anchor='n', fill='y')

tk.Label(panel, text='SANDBOX ', font=('Courier', 17, 'bold'), bg='#f8f0dd', fg='#41664d').pack(pady=(0, 8))
tk.Label(panel, text='ELEMENTOS', font=('Courier', 12, 'bold'), bg='#f8f0dd').pack()

marco_iconos = tk.Frame(panel, bg='#f8f0dd')
marco_iconos.pack(pady=8)
botones_elementos = {}
imagenes_iconos = {}

for indice, (elemento, nombre) in enumerate(nombres.items()):
    archivo = 'borrador.png' if elemento == Elemento.aire else nombre.lower() + '.png'
    imagen = cargar_png('iconos', archivo).resize((34, 34), Image.Resampling.NEAREST)
    imagenes_iconos[elemento] = ImageTk.PhotoImage(imagen)
    cuadro = tk.Frame(marco_iconos, bg='#e8dfce', padx=5, pady=4, relief='ridge', bd=2)
    cuadro.grid(row=indice // 4, column=indice % 4, padx=3, pady=3)
    icono = tk.Label(cuadro, image=imagenes_iconos[elemento], bg='#e8dfce', cursor='hand2')
    icono.pack()
    texto = tk.Label(cuadro, text=nombre, font=('Courier', 8), bg='#e8dfce', cursor='hand2')
    texto.pack()
    for widget in (cuadro, icono, texto):
        widget.bind('<Button-1>', lambda evento, elegido=elemento: seleccionar_elemento(elegido))
    botones_elementos[elemento] = cuadro

etiqueta_seleccion = tk.Label(panel, text='', font=('Courier', 10, 'bold'), bg='#f8f0dd', fg='#41664d')
etiqueta_seleccion.pack(pady=4)

tk.Label(panel, text='TAMAÑO DEL PINCEL', font=('Courier', 10, 'bold'), bg='#f8f0dd').pack(pady=(8, 0))
escala_pincel = tk.Scale(panel, from_=1, to=5, orient='horizontal', bg='#f8f0dd', highlightthickness=0, command=cambiar_tamano_pincel)
escala_pincel.pack()
escala_pincel.set(1)

tk.Label(panel, text='SIMULACIÓN', font=('Courier', 12, 'bold'), bg='#f8f0dd').pack(pady=(8, 4))
boton_pausa = tk.Button(panel, text='⏸ Pausar', width=22, command=pausar_continuar)
boton_pausa.pack(pady=2)
boton_rectangulo = tk.Button(panel, text='▣ Rectángulo: OFF', width=22, command=activar_rectangulo)
boton_rectangulo.pack(pady=2)
tk.Button(panel, text='Limpiar mundo', width=22, command=limpiar_mundo).pack(pady=2)

tk.Label(panel, text='TAMAÑO DE MATRIZ', font=('Courier', 10, 'bold'), bg='#f8f0dd').pack(pady=(8, 0))
escala_matriz = tk.Scale(panel, from_=20, to=100, orient='horizontal', bg='#f8f0dd', highlightthickness=0)
escala_matriz.pack()
escala_matriz.set(simulador.tamano)
tk.Button(panel, text='Aplicar tamaño', width=22, command=cambiar_tamano_matriz).pack(pady=2)

tk.Label(panel, text='ARCHIVOS', font=('Courier', 12, 'bold'), bg='#f8f0dd').pack(pady=(8, 4))
tk.Button(panel, text='Guardar mundo', width=22, command=guardar_mundo).pack(pady=2)
tk.Button(panel, text='Cargar mundo', width=22, command=cargar_mundo).pack(pady=2)

etiqueta_estado = tk.Label(panel, text='Pincel libre', font=('Courier', 9), bg='#f8f0dd', fg='#41664d')
etiqueta_estado.pack(pady=8)

lienzo.bind('<Button-1>', pintar)
lienzo.bind('<B1-Motion>', pintar_arrastrando)
seleccionar_elemento(Elemento.arena)
reconstruir_lienzo()
actualizar_mundo()
ventana.mainloop()
