import tkinter as tk
import os
from PIL import Image, ImageTk, ImageSequence

GIF_PATH = os.path.join(os.path.dirname(__file__), "Aviso.gif")
MARCADOR = os.path.join(os.path.dirname(__file__), ".aviso_visto")

WIN_W, WIN_H = 960, 540


class PantallaAviso:
    def __init__(self, on_finish=None):
        self.on_finish = on_finish
        self.root = tk.Tk()
        self.root.title("Érebo")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - WIN_W) // 2
        y = (screen_h - WIN_H) // 2
        self.root.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

        self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        gif = Image.open(GIF_PATH)
        self.frames = []
        self.delays = []
        for frame in ImageSequence.Iterator(gif):
            self.delays.append(frame.info.get("duration", 60))
            resized = frame.convert("RGB").resize((WIN_W, WIN_H), Image.LANCZOS)
            self.frames.append(ImageTk.PhotoImage(resized))

        self.index = 0
        self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.frames[0])

        # Nota: el gif no trae un botón "Omitir" dibujado, así que se puede
        # omitir haciendo click en cualquier parte de la pantalla o
        # presionando cualquier tecla (se avisa igual con un texto sutil).
        self.canvas.create_text(
            WIN_W - 90, WIN_H - 24, text="Omitir  →", fill="#c9b8f5",
            font=("Arial", 11, "bold")
        )
        self.canvas.bind("<Button-1>", lambda e: self._omitir())
        self.root.bind("<Key>", lambda e: self._omitir())
        self.canvas.config(cursor="hand2")

        self._animar()

    def _animar(self):
        self.canvas.itemconfig(self.image_id, image=self.frames[self.index])
        delay = self.delays[self.index]
        self.index = (self.index + 1) % len(self.frames)
        self._loop_id = self.root.after(delay, self._animar)

    def _omitir(self):
        try:
            with open(MARCADOR, "w") as f:
                f.write("visto")
        except OSError:
            pass
        self.root.destroy()
        if self.on_finish:
            self.on_finish()

    def run(self):
        self.root.mainloop()


def abrir_aviso(on_finish=None):
    if os.path.exists(MARCADOR):
        # Ya se mostró antes: se salta directo.
        if on_finish:
            on_finish()
        return
    pantalla = PantallaAviso(on_finish=on_finish)
    pantalla.run()


if __name__ == "__main__":
    abrir_aviso(on_finish=lambda: print("Aviso omitido"))
