"""
Punto de entrada único de Érebo.

Orden de ejecución:
    1. Pantalla de carga      (loading.gif)
    2. Pantalla de advertencia (advertencia.gif)
    3. App principal Érebo    (fondo animado erebo_fondo.gif + cifrado por cámara)

Requisitos:
    pip install pillow opencv-python cryptography

Uso:
    python main.py
"""

import tkinter as tk

from pantalla_de_carga import abrir_carga
from pantalla_de_advertencia import abrir_advertencia
from erebo_app import EreboApp


def iniciar_app_principal():
    root = tk.Tk()
    EreboApp(root)
    root.mainloop()


def iniciar_advertencia():
    abrir_advertencia(on_finish=iniciar_app_principal)


if __name__ == "__main__":
    abrir_carga(on_finish=iniciar_advertencia)
