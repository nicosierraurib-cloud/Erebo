import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import hashlib
import base64
import os
from cryptography.fernet import Fernet

class EreboApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Érebo Engine - Cifrado por Entropía")
        self.root.geometry("500x350")
        self.root.configure(padx=20, pady=20)

        tk.Label(root, text="Érebo", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(root, text="Asegúrate de tapar la cámara antes de generar la clave.").pack()

        tk.Label(root, text="Texto a encriptar/desencriptar:").pack(anchor="w", pady=(10,0))
        self.text_input = tk.Entry(root, width=50)
        self.text_input.pack(pady=5)

        frame_text_btns = tk.Frame(root)
        frame_text_btns.pack(pady=5)
        tk.Button(frame_text_btns, text="Cifrar Texto", command=self.encrypt_text).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_text_btns, text="Descifrar Texto", command=self.decrypt_text).pack(side=tk.LEFT, padx=5)

        tk.Frame(root, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=15)

        tk.Label(root, text="Cifrado de Archivos (Sobrescribe el archivo original):").pack(anchor="w")
        frame_file_btns = tk.Frame(root)
        frame_file_btns.pack(pady=5)
        tk.Button(frame_file_btns, text="Cifrar Archivo", command=self.encrypt_file).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_file_btns, text="Descifrar Archivo", command=self.decrypt_file).pack(side=tk.LEFT, padx=5)

    def _get_camera_key(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "No se pudo acceder a la cámara.")
            return None

        ret, frame = cap.read()
        cap.release()

        if ret:
            raw_bytes = frame.tobytes()
            key_bytes = hashlib.sha256(raw_bytes).digest()
            return base64.urlsafe_b64encode(key_bytes)
        else:
            messagebox.showerror("Error", "No se pudo leer el sensor.")
            return None

    def encrypt_text(self):
        key = self._get_camera_key()
        if not key: return

        texto = self.text_input.get().encode()
        try:
            f = Fernet(key)
            token = f.encrypt(texto)
            self.text_input.delete(0, tk.END)
            self.text_input.insert(0, token.decode())
            messagebox.showinfo("Éxito", f"Texto cifrado.\n\nGuarda esta clave para descifrarlo:\n{key.decode()}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def decrypt_text(self):
        key_str = tk.simpledialog.askstring("Clave requerida", "Pega la clave de 44 caracteres generada:")
        if not key_str: return

        texto_cifrado = self.text_input.get().encode()
        try:
            f = Fernet(key_str.encode())
            texto_claro = f.decrypt(texto_cifrado)
            self.text_input.delete(0, tk.END)
            self.text_input.insert(0, texto_claro.decode())
            messagebox.showinfo("Éxito", "Texto descifrado correctamente.")
        except Exception:
            messagebox.showerror("Error", "Clave incorrecta o texto corrupto.")

    def encrypt_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath: return

        key = self._get_camera_key()
        if not key: return

        try:
            with open(filepath, 'rb') as file:
                data = file.read()

            f = Fernet(key)
            encrypted_data = f.encrypt(data)

            with open(filepath, 'wb') as file:
                file.write(encrypted_data)

            messagebox.showinfo("Éxito", f"Archivo cifrado.\n\nGuarda esta clave para descifrarlo:\n{key.decode()}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo: {e}")

    def decrypt_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath: return

        key_str = tk.simpledialog.askstring("Clave requerida", "Pega la clave generada:")
        if not key_str: return

        try:
            with open(filepath, 'rb') as file:
                encrypted_data = file.read()

            f = Fernet(key_str.encode())
            decrypted_data = f.decrypt(encrypted_data)

            with open(filepath, 'wb') as file:
                file.write(decrypted_data)

            messagebox.showinfo("Éxito", "Archivo descifrado correctamente.")
        except Exception:
            messagebox.showerror("Error", "Clave incorrecta o archivo corrupto.")

if __name__ == "__main__":
    root = tk.Tk()
    app = EreboApp(root)
    root.mainloop()
