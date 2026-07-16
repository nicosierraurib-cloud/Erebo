import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os

GIF_PATH = os.path.join(os.path.dirname(__file__), "loading.gif")

TIEMPO_MINIMO_MS = 6470


class SplashScreen:
    def __init__(self, gif_path, on_finish=None, min_display_time=None):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.on_finish = on_finish

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
        """Cierra la pantalla de carga y abre la app principal."""
        self.root.destroy()
        if self.on_finish:
            self.on_finish()

    def run(self):
        self.root.mainloop()


def abrir_carga(on_finish=None):
    """Punto de entrada para usar esta pantalla desde otro script (ej. main.py)."""
    splash = SplashScreen(
        GIF_PATH, on_finish=on_finish, min_display_time=TIEMPO_MINIMO_MS
    )
    splash.run()


def abrir_app_principal():
    """Reemplaza esto con tu app real (solo se usa al correr este archivo solo)."""
    root = tk.Tk()
    root.title("Erebo")
    root.geometry("500x300")
    tk.Label(root, text="Carga Exitosa", font=("Arial", 16)).pack(
        expand=True
    )
    root.mainloop()


if __name__ == "__main__":
    splash = SplashScreen(
        GIF_PATH, on_finish=abrir_app_principal, min_display_time=TIEMPO_MINIMO_MS
    )
    splash.run()
