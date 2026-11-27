import os
import tempfile
import unittest

from configuracion import Elemento
from simulador import Simulador


class PruebasSimulador(unittest.TestCase):
    def test_matriz_cuadrada_y_limites(self):
        mundo = Simulador(tamano=20)
        self.assertEqual(len(mundo.matriz), 20)
        self.assertTrue(all(len(fila) == 20 for fila in mundo.matriz))
        mundo.redimensionar(100)
        self.assertEqual(mundo.tamano, 100)
        self.assertTrue(all(len(fila) == 100 for fila in mundo.matriz))

    def test_pincel_cuadrado(self):
        mundo = Simulador(tamano=20)
        mundo.cambiar_pincel(3)
        mundo.dibujar(10, 10, Elemento.piedra)
        for fila in range(9, 12):
            for columna in range(9, 12):
                self.assertEqual(mundo.celda(fila, columna), Elemento.piedra)

    def test_rectangulo_inclusivo(self):
        mundo = Simulador(tamano=20)
        mundo.rellenar(7, 8, 3, 5, Elemento.arena)
        for fila in range(3, 8):
            for columna in range(5, 9):
                self.assertEqual(mundo.celda(fila, columna), Elemento.arena)

    def test_agua_convierte_tierra_en_pasto(self):
        mundo = Simulador(tamano=20)
        mundo.dibujar(5, 5, Elemento.tierra)
        mundo.dibujar(4, 5, Elemento.agua)
        mundo.avanzar()
        self.assertEqual(mundo.celda(5, 5), Elemento.pasto)

    def test_semilla_germina_y_crece(self):
        mundo = Simulador(tamano=20)
        mundo.dibujar(10, 5, Elemento.tierra)
        mundo.dibujar(9, 5, Elemento.semilla)
        mundo.dibujar(10, 6, Elemento.agua)
        mundo.avanzar(2)
        self.assertIn(mundo.celda(9, 5), (
            Elemento.planta_1,
            Elemento.planta_2,
            Elemento.planta_3,
        ))
        mundo.avanzar(20)
        self.assertEqual(mundo.celda(9, 5), Elemento.planta_3)

    def test_agua_apaga_fuego(self):
        mundo = Simulador(tamano=20)
        mundo.dibujar(5, 5, Elemento.fuego)
        mundo.dibujar(4, 5, Elemento.agua)
        mundo.avanzar()
        self.assertNotEqual(mundo.celda(5, 5), Elemento.fuego)

    def test_animal_evita_agua_y_obstaculos(self):
        mundo = Simulador(tamano=20)
        mundo.rellenar(13, 5, 13, 9, Elemento.piedra)
        mundo.dibujar(12, 8, Elemento.agua)
        mundo.dibujar(12, 9, Elemento.piedra)
        mundo.dibujar(12, 7, Elemento.animal)
        mundo.avanzar(3)
        self.assertEqual(mundo.celda(12, 8), Elemento.agua)
        self.assertEqual(mundo.celda(12, 7), Elemento.animal)

    def test_animal_muere_cerca_del_fuego(self):
        mundo = Simulador(tamano=20)
        mundo.dibujar(12, 6, Elemento.animal)
        mundo.dibujar(11, 6, Elemento.piedra)
        mundo.dibujar(12, 7, Elemento.fuego)
        mundo.avanzar()
        self.assertEqual(mundo.celda(12, 6), Elemento.aire)

    def test_guardar_y_cargar(self):
        mundo = Simulador(tamano=20)
        mundo.dibujar(8, 8, Elemento.piedra)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "mapa.json")
            mundo.guardar(ruta)
            cargado = Simulador(tamano=40)
            cargado.cargar(ruta)
            self.assertEqual(cargado.tamano, 20)
            self.assertEqual(cargado.celda(8, 8), Elemento.piedra)


if __name__ == "__main__":
    unittest.main()
