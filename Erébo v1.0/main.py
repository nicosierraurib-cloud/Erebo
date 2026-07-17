"""
Punto de entrada único de Érebo v2.

Orden de ejecución:
    1. Se enciende la cámara YA (para que esté lista/estabilizada cuando
       el usuario llegue a la pantalla de cifrado).
    2. Pantalla de carga   (Carga.gif)      -> no hace nada, solo da tiempo.
    3. Pantalla de aviso   (Aviso.gif)      -> SOLO la primera vez que se instala.
    4. App principal (Cifrar / Descifrar)   -> navegación con las flechas
       izquierda/derecha del teclado, botón de salir con animación (Salida.gif).

Funciona igual en Windows y en Linux (no usa nada específico del sistema).

Requisitos:
    pip install pillow opencv-python cryptography

Uso:
    python main.py
"""

import tkinter as tk
import cv2

from pantalla_de_carga import abrir_carga
from pantalla_de_aviso import abrir_aviso
from erebo_app import EreboApp


def iniciar_app_principal(cap):
    root = tk.Tk()
    EreboApp(root, cap)
    root.mainloop()


def iniciar_aviso(cap):
    abrir_aviso(on_finish=lambda: iniciar_app_principal(cap))


if __name__ == "__main__":
    # La cámara se abre lo antes posible para que esté estabilizada
    # (exposición/enfoque) cuando el usuario llegue a cifrar algo.
    cap = cv2.VideoCapture(0)

    abrir_carga(on_finish=lambda: iniciar_aviso(cap))
