"""
Pantalla de advertencia para Tkinter.
Reproduce advertencia.gif en bucle, independiente de la pantalla de carga.
El gif vive junto a este script, sin depender de internet.

Requisitos:
    pip install pillow

Uso:
    python pantalla_de_advertencia.py

Para encadenarla después de la pantalla de carga, en tu pantalla_de_carga.py
reemplaza on_finish=abrir_app_principal por on_finish=abrir_advertencia
(importando esta función desde este archivo).
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os

GIF_PATH = os.path.join(os.path.dirname(__file__), "advertencia.gif")

# Cuánto tiempo mínimo (en ms) se muestra la pantalla de advertencia.
# Ponlo en None si quieres que se cierre apenas el usuario continúe,
# o dale un valor fijo si prefieres que siempre se vea completa al menos una vez.
TIEMPO_MINIMO_MS = 6382  # ~ duración del video original


class WarningScreen:
    def __init__(self, gif_path, on_finish=None, min_display_time=None):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # sin bordes ni barra de título
        self.on_finish = on_finish

        # Cargar todos los frames del GIF con Pillow
        img = Image.open(gif_path)
        self.frames = []
        self.delays = []
        for frame in ImageSequence.Iterator(img):
            self.frames.append(ImageTk.PhotoImage(frame.convert("RGBA")))
            self.delays.append(frame.info.get("duration", 100))

        w, h = img.size

        # Centrar la ventana en la pantalla
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.label = tk.Label(self.root, bd=0)
        self.label.pack()

        self.frame_index = 0
        self._animate()

        if min_display_time:
            self.root.after(min_display_time, self.finish)

    def _animate(self):
        frame = self.frames[self.frame_index]
        delay = self.delays[self.frame_index]
        self.label.configure(image=frame)
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.root.after(delay, self._animate)

    def finish(self):
        """Cierra la pantalla de advertencia y continúa con lo que sigue."""
        self.root.destroy()
        if self.on_finish:
            self.on_finish()

    def run(self):
        self.root.mainloop()


def abrir_advertencia(on_finish=None):
    """Punto de entrada para usar esta pantalla desde otro script (ej. encadenada
    después de la pantalla de carga)."""
    warning = WarningScreen(
        GIF_PATH, on_finish=on_finish, min_display_time=TIEMPO_MINIMO_MS
    )
    warning.run()


def abrir_app_principal():
    """Reemplaza esto con tu app real."""
    root = tk.Tk()
    root.title("Mi App")
    root.geometry("500x300")
    tk.Label(root, text="¡Tu app cargó correctamente!", font=("Arial", 16)).pack(
        expand=True
    )
    root.mainloop()


if __name__ == "__main__":
    abrir_advertencia(on_finish=abrir_app_principal)
