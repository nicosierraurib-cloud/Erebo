import tkinter as tk
import os
from PIL import Image, ImageTk, ImageSequence

GIF_PATH = os.path.join(os.path.dirname(__file__), "Carga.gif")

WIN_W, WIN_H = 960, 540


class PantallaCarga:
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
        self._reproducir()

    def _reproducir(self):
        self.canvas.itemconfig(self.image_id, image=self.frames[self.index])
        delay = self.delays[self.index]
        self.index += 1
        if self.index < len(self.frames):
            self.root.after(delay, self._reproducir)
        else:
            self.root.after(delay, self._terminar)

    def _terminar(self):
        self.root.destroy()
        if self.on_finish:
            self.on_finish()

    def run(self):
        self.root.mainloop()


def abrir_carga(on_finish=None):
    pantalla = PantallaCarga(on_finish=on_finish)
    pantalla.run()


if __name__ == "__main__":
    abrir_carga(on_finish=lambda: print("Carga terminada"))
