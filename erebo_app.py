import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import cv2
import hashlib
import base64
import os
from cryptography.fernet import Fernet
from PIL import Image, ImageTk, ImageSequence

GIF_FONDO = os.path.join(os.path.dirname(__file__), "erebo_fondo.gif")


class EreboApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Érebo Engine - Cifrado por Entropía")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        self.cap = cv2.VideoCapture(0)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ---------- Fondo animado ----------
        self.canvas = tk.Canvas(root, width=500, height=350, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.bg_frames = []
        self.bg_delays = []
        bg_img = Image.open(GIF_FONDO)
        for frame in ImageSequence.Iterator(bg_img):
            self.bg_frames.append(ImageTk.PhotoImage(frame.convert("RGB").resize((500, 350))))
            self.bg_delays.append(frame.info.get("duration", 66))

        self.bg_frame_index = 0
        self.bg_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.bg_frames[0])
        self._animate_bg()

        # ---------- Controles encima del fondo ----------
        # Se usa un frame semitransparente (en Tk no hay alpha real, así que
        # usamos negro sólido a juego con el video, que es oscuro).
        panel = tk.Frame(self.canvas, bg="black", bd=0)
        self.canvas.create_window(250, 175, window=panel, anchor="center")

        FG = "white"
        BG = "black"

        tk.Label(panel, text="Érebo", font=("Arial", 16, "bold"), fg=FG, bg=BG).pack(pady=(10, 0))
        tk.Label(
            panel,
            text="Asegúrate de tapar la cámara antes de generar la clave.",
            fg=FG, bg=BG,
        ).pack()

        tk.Label(panel, text="Texto a encriptar/desencriptar:", fg=FG, bg=BG).pack(anchor="w", pady=(10, 0))
        self.text_input = tk.Entry(panel, width=50)
        self.text_input.pack(pady=5)

        frame_text_btns = tk.Frame(panel, bg=BG)
        frame_text_btns.pack(pady=5)
        tk.Button(frame_text_btns, text="Cifrar Texto", command=self.encrypt_text).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_text_btns, text="Descifrar Texto", command=self.decrypt_text).pack(side=tk.LEFT, padx=5)

        tk.Frame(panel, height=2, bd=1, relief=tk.SUNKEN, bg="gray").pack(fill=tk.X, pady=15)

        tk.Label(panel, text="Cifrado de Archivos (Sobrescribe el archivo original):", fg=FG, bg=BG).pack(anchor="w")
        frame_file_btns = tk.Frame(panel, bg=BG)
        frame_file_btns.pack(pady=5)
        tk.Button(frame_file_btns, text="Cifrar Archivo", command=self.encrypt_file).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_file_btns, text="Descifrar Archivo", command=self.decrypt_file).pack(side=tk.LEFT, padx=5)

    def _animate_bg(self):
        self.bg_frame_index = (self.bg_frame_index + 1) % len(self.bg_frames)
        self.canvas.itemconfig(self.bg_image_id, image=self.bg_frames[self.bg_frame_index])
        delay = self.bg_delays[self.bg_frame_index]
        self.root.after(delay, self._animate_bg)

    def _get_camera_key(self):
        if not self.cap.isOpened():
            messagebox.showerror("Error", "No se pudo acceder a la cámara.")
            return None

        for _ in range(5):
            self.cap.read()

        ret, frame = self.cap.read()

        if ret:
            raw_bytes = frame.tobytes()
            key_bytes = hashlib.sha256(raw_bytes).digest()
            return base64.urlsafe_b64encode(key_bytes)
        else:
            messagebox.showerror("Error", "No se pudo leer el sensor.")
            return None

    def encrypt_text(self):
        key = self._get_camera_key()
        if not key:
            return

        texto = self.text_input.get().encode()
        try:
            f = Fernet(key)
            token = f.encrypt(texto)
            self.text_input.delete(0, tk.END)
            self.text_input.insert(0, token.decode())

            key_str = key.decode()
            self.root.clipboard_clear()
            self.root.clipboard_append(key_str)
            self.root.update()

            with open("texto_cifrado.key", "w") as kf:
                kf.write(key_str)

            messagebox.showinfo(
                "Éxito",
                f"Texto cifrado.\n\nLa clave se copió al portapapeles y se guardó en 'texto_cifrado.key'",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def decrypt_text(self):
        key_str = simpledialog.askstring("Clave requerida", "Pega la clave de 44 caracteres generada:")
        if not key_str:
            return

        texto_cifrado = self.text_input.get().encode()
        try:
            f = Fernet(key_str.strip().encode())
            texto_claro = f.decrypt(texto_cifrado)
            self.text_input.delete(0, tk.END)
            self.text_input.insert(0, texto_claro.decode())
            messagebox.showinfo("Éxito", "Texto descifrado correctamente.")
        except Exception:
            messagebox.showerror("Error", "Clave incorrecta o texto corrupto.")

    def encrypt_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return

        key = self._get_camera_key()
        if not key:
            return

        try:
            with open(filepath, "rb") as file:
                data = file.read()

            f = Fernet(key)
            encrypted_data = f.encrypt(data)

            with open(filepath, "wb") as file:
                file.write(encrypted_data)

            key_str = key.decode()
            self.root.clipboard_clear()
            self.root.clipboard_append(key_str)
            self.root.update()

            key_filepath = filepath + ".key"
            with open(key_filepath, "w") as kf:
                kf.write(key_str)

            messagebox.showinfo(
                "Éxito",
                f"Archivo cifrado.\n\nLa clave se copió al portapapeles y se guardó en:\n{key_filepath}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo: {e}")

    def decrypt_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return

        key_str = simpledialog.askstring("Clave requerida", "Pega la clave generada:")
        if not key_str:
            return

        try:
            with open(filepath, "rb") as file:
                encrypted_data = file.read()

            f = Fernet(key_str.strip().encode())
            decrypted_data = f.decrypt(encrypted_data)

            with open(filepath, "wb") as file:
                file.write(decrypted_data)

            messagebox.showinfo("Éxito", "Archivo descifrado correctamente.")
        except Exception:
            messagebox.showerror("Error", "Clave incorrecta o archivo corrupto.")

    def on_closing(self):
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = EreboApp(root)
    root.mainloop()
