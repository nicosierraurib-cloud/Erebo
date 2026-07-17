import tkinter as tk
from tkinter import filedialog, messagebox
import hashlib
import base64
import os
import json
import datetime
from cryptography.fernet import Fernet
from PIL import Image, ImageTk, ImageSequence

DIR_APP = os.path.dirname(__file__)

GIF_CIFRAR = os.path.join(DIR_APP, "Cifrar.gif")
GIF_DESCIFRAR = os.path.join(DIR_APP, "Descifrar.gif")
GIF_SALIDA = os.path.join(DIR_APP, "Salida.gif")
REGISTRO_PATH = os.path.join(DIR_APP, "claves_registro.json")

WIN_W, WIN_H = 960, 540

# Coordenadas de las cajas, medidas sobre el frame de referencia de cada gif
# (los gifs originales son de 1920x1080). Se guardan como fracciones para
# poder escalarlas a WIN_W x WIN_H.
REF_W, REF_H = 1920, 1080

CAJAS_CIFRAR = {
    "imagen":      (152, 483, 633, 973),
    "documentos":  (726, 483, 1207, 973),
    "carpetas":    (1299, 483, 1780, 973),
}

PANEL_DESCIFRAR = (125, 197, 1795, 687)

# Paleta sacada directamente del propio gif (para que el texto que dibujamos
# encima del panel se sienta parte del mismo diseño, no un widget pegado).
TEXTO_CLARO = "#f4f1fb"
TEXTO_MUTED = "#b9aed6"
ACENTO = "#c9a6ff"
HOVER_FILL = "#584c7a"

FILA_ALTO = 34
PADDING_PANEL = 22


# ==========================================================================
# Registro local de claves generadas (independiente de dónde esté el
# archivo/carpeta original). Esto es lo que alimenta el panel de "Descifrar".
# ==========================================================================
def cargar_registro():
    if not os.path.exists(REGISTRO_PATH):
        return []
    try:
        with open(REGISTRO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def guardar_registro(lista):
    with open(REGISTRO_PATH, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)


def agregar_clave(tipo, ruta, key_str, archivos=None):
    registro = cargar_registro()
    registro.append({
        "tipo": tipo,  # "imagen" | "documento" | "carpeta"
        "ruta": ruta,
        "clave": key_str,
        "archivos": archivos or [],
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    guardar_registro(registro)


def quitar_clave(indice):
    registro = cargar_registro()
    if 0 <= indice < len(registro):
        registro.pop(indice)
        guardar_registro(registro)


class EreboApp:
    def __init__(self, root, cap):
        self.root = root
        self.cap = cap  # la cámara ya viene abierta desde main.py
        self.root.title("Érebo Engine - Cifrado por Entropía")
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.salir)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - WIN_W) // 2
        y = (screen_h - WIN_H) // 2
        self.root.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

        self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        # ---------- Fondos animados de cada pantalla (loop continuo) ----------
        self.frames_cifrar, self.delays_cifrar = self._cargar_gif(GIF_CIFRAR)
        self.frames_descifrar, self.delays_descifrar = self._cargar_gif(GIF_DESCIFRAR)

        self.bg_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.frames_cifrar[0])

        # Cajas/panel ya escalados a WIN_W x WIN_H (nada dibujado encima,
        # el diseño ya viene completo en el gif; solo detectamos clicks ahí)
        self.cajas_cifrar_px = self._escalar_cajas(CAJAS_CIFRAR)
        self.panel_descifrar_px = self._escalar_caja(PANEL_DESCIFRAR)

        self.pagina = "cifrar"
        self._indices = {"cifrar": 0, "descifrar": 0}
        self.scroll_offset = 0
        self.entradas_render = []  # [(y1, y2, indice_registro), ...] de la vista actual
        self.entrada_hover = None
        self.hover_rect_id = None

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<MouseWheel>", self._on_scroll)      # Windows / macOS
        self.canvas.bind("<Button-4>", lambda e: self._on_scroll_linux(-1))
        self.canvas.bind("<Button-5>", lambda e: self._on_scroll_linux(1))
        self.root.bind("<Left>", lambda e: self.mostrar_pagina("cifrar"))
        self.root.bind("<Right>", lambda e: self.mostrar_pagina("descifrar"))
        self.root.bind("<Escape>", lambda e: self.salir())

        self.mostrar_pagina("cifrar")
        self._animar_fondo()

    # ------------------------------------------------------------------
    def _cargar_gif(self, path):
        gif = Image.open(path)
        frames, delays = [], []
        for frame in ImageSequence.Iterator(gif):
            delays.append(frame.info.get("duration", 70))
            resized = frame.convert("RGB").resize((WIN_W, WIN_H), Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(resized))
        return frames, delays

    def _escalar_caja(self, box):
        x1, y1, x2, y2 = box
        return (
            x1 / REF_W * WIN_W, y1 / REF_H * WIN_H,
            x2 / REF_W * WIN_W, y2 / REF_H * WIN_H,
        )

    def _escalar_cajas(self, cajas):
        return {nombre: self._escalar_caja(box) for nombre, box in cajas.items()}

    # ------------------------------------------------------------------
    # Panel de Descifrar: texto dibujado a mano sobre el panel del propio
    # gif (nada de widgets nativos ni cajas propias encima).
    # ------------------------------------------------------------------
    def _dibujar_lista_claves(self):
        # Limpia lo dibujado antes
        self.canvas.delete("entrada_clave")
        if self.hover_rect_id:
            self.canvas.delete(self.hover_rect_id)
            self.hover_rect_id = None
        self.entradas_render = []

        x1, y1, x2, y2 = self.panel_descifrar_px
        registro = cargar_registro()
        self.registro = registro

        if not registro:
            self.canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2,
                text="(todavía no hay claves generadas)",
                fill=TEXTO_MUTED, font=("Arial", 11, "italic"),
                tags="entrada_clave"
            )
            return

        etiquetas = {"imagen": "Imagen", "documento": "Documento", "carpeta": "Carpeta"}
        area_alto = (y2 - y1) - 2 * PADDING_PANEL
        filas_visibles = max(1, int(area_alto // FILA_ALTO))

        max_offset = max(0, len(registro) - filas_visibles)
        self.scroll_offset = min(self.scroll_offset, max_offset)

        visibles = registro[self.scroll_offset: self.scroll_offset + filas_visibles]

        fila_y = y1 + PADDING_PANEL
        for i, entrada in enumerate(visibles):
            indice_real = self.scroll_offset + i
            nombre = os.path.basename(entrada["ruta"].rstrip("/\\"))
            etiqueta = etiquetas.get(entrada["tipo"], entrada["tipo"])

            self.canvas.create_text(
                x1 + 24, fila_y + FILA_ALTO / 2,
                text=etiqueta, fill=ACENTO, font=("Arial", 10, "bold"),
                anchor="w", tags="entrada_clave"
            )
            self.canvas.create_text(
                x1 + 110, fila_y + FILA_ALTO / 2,
                text=nombre, fill=TEXTO_CLARO, font=("Arial", 11),
                anchor="w", tags="entrada_clave"
            )
            self.canvas.create_text(
                x2 - 24, fila_y + FILA_ALTO / 2,
                text=entrada["fecha"], fill=TEXTO_MUTED, font=("Arial", 9),
                anchor="e", tags="entrada_clave"
            )
            self.entradas_render.append((fila_y, fila_y + FILA_ALTO, indice_real))
            fila_y += FILA_ALTO

        if len(registro) > filas_visibles:
            self.canvas.create_text(
                (x1 + x2) / 2, y2 - PADDING_PANEL / 2,
                text=f"▲▼ desplázate para ver más ({len(registro)} en total)",
                fill=TEXTO_MUTED, font=("Arial", 9, "italic"),
                tags="entrada_clave"
            )

        # el hover se redibuja según la posición actual del mouse
        self._actualizar_hover(self.root.winfo_pointerx() - self.root.winfo_rootx(),
                                self.root.winfo_pointery() - self.root.winfo_rooty())

    def _entrada_en(self, x, y):
        x1, y1, x2, y2 = self.panel_descifrar_px
        if not (x1 <= x <= x2 and y1 <= y <= y2):
            return None
        for fy1, fy2, indice in self.entradas_render:
            if fy1 <= y <= fy2:
                return indice
        return None

    def _actualizar_hover(self, x, y):
        if self.pagina != "descifrar":
            return
        indice = self._entrada_en(x, y)
        if self.hover_rect_id:
            self.canvas.delete(self.hover_rect_id)
            self.hover_rect_id = None
        if indice is not None:
            x1, y1, x2, y2 = self.panel_descifrar_px
            for fy1, fy2, idx in self.entradas_render:
                if idx == indice:
                    self.hover_rect_id = self.canvas.create_rectangle(
                        x1 + 8, fy1, x2 - 8, fy2,
                        fill=HOVER_FILL, outline="", stipple="gray25",
                        tags="entrada_clave"
                    )
                    self.canvas.tag_lower(self.hover_rect_id, "entrada_clave")
                    break

    def _restaurar_indice(self, indice):
        registro = cargar_registro()
        if indice < 0 or indice >= len(registro):
            return
        entrada = registro[indice]

        confirmar = messagebox.askyesno(
            "Restaurar",
            f"¿Restaurar {entrada['tipo']} '{os.path.basename(entrada['ruta'])}'\ncon la clave guardada?"
        )
        if not confirmar:
            return

        try:
            key = entrada["clave"].encode()
            if entrada["tipo"] == "carpeta":
                for fpath in entrada["archivos"]:
                    if not os.path.exists(fpath):
                        continue
                    with open(fpath, "rb") as fh:
                        data = fh.read()
                    data_clara = Fernet(key).decrypt(data)
                    with open(fpath, "wb") as fh:
                        fh.write(data_clara)
                messagebox.showinfo("Éxito", "Carpeta restaurada correctamente.")
            else:
                fpath = entrada["ruta"]
                with open(fpath, "rb") as fh:
                    data = fh.read()
                data_clara = Fernet(key).decrypt(data)
                with open(fpath, "wb") as fh:
                    fh.write(data_clara)
                messagebox.showinfo("Éxito", "Archivo restaurado correctamente.")

            quitar_clave(indice)
            self._dibujar_lista_claves()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar: {e}")

    def _on_scroll(self, event):
        if self.pagina != "descifrar":
            return
        self.scroll_offset += -1 if event.delta > 0 else 1
        self.scroll_offset = max(0, self.scroll_offset)
        self._dibujar_lista_claves()

    def _on_scroll_linux(self, direccion):
        if self.pagina != "descifrar":
            return
        self.scroll_offset = max(0, self.scroll_offset + direccion)
        self._dibujar_lista_claves()

    # ------------------------------------------------------------------
    # Navegación entre páginas (flechas del teclado)
    # ------------------------------------------------------------------
    def mostrar_pagina(self, nombre):
        if nombre == self.pagina:
            return
        self.pagina = nombre
        if nombre == "cifrar":
            self.canvas.delete("entrada_clave")
        else:
            self.scroll_offset = 0
            self._dibujar_lista_claves()

    def _animar_fondo(self):
        if self.pagina == "cifrar":
            frames, delays = self.frames_cifrar, self.delays_cifrar
        else:
            frames, delays = self.frames_descifrar, self.delays_descifrar

        i = self._indices[self.pagina]
        self.canvas.itemconfig(self.bg_image_id, image=frames[i])
        delay = delays[i]
        self._indices[self.pagina] = (i + 1) % len(frames)
        self.root.after(delay, self._animar_fondo)

    # ------------------------------------------------------------------
    # Clicks
    # ------------------------------------------------------------------
    def _caja_cifrar_en(self, x, y):
        for nombre, (x1, y1, x2, y2) in self.cajas_cifrar_px.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return nombre
        return None

    def _on_motion(self, event):
        if self.pagina == "cifrar":
            caja = self._caja_cifrar_en(event.x, event.y)
            self.canvas.config(cursor="hand2" if caja else "")
        else:
            indice = self._entrada_en(event.x, event.y)
            self.canvas.config(cursor="hand2" if indice is not None else "")
            self._actualizar_hover(event.x, event.y)

    def _on_click(self, event):
        if self.pagina == "cifrar":
            caja = self._caja_cifrar_en(event.x, event.y)
            if caja == "imagen":
                self.encrypt_image()
            elif caja == "documentos":
                self.encrypt_document()
            elif caja == "carpetas":
                self.encrypt_folder()

    def _on_right_click(self, event):
        if self.pagina == "descifrar":
            indice = self._entrada_en(event.x, event.y)
            if indice is not None:
                self._restaurar_indice(indice)

    # ------------------------------------------------------------------
    # Salida animada
    # ------------------------------------------------------------------
    def salir(self):
        frames, delays = self._cargar_gif(GIF_SALIDA)
        self.canvas.delete("entrada_clave")
        self.canvas.itemconfig(self.bg_image_id, image=frames[0])
        self._frames_salida = frames  # mantener referencia viva
        self.root.after(1800, self._cerrar_definitivamente)

    def _cerrar_definitivamente(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

    # ------------------------------------------------------------------
    # Cámara -> clave de cifrado (idéntico al método original de Érebo)
    # ------------------------------------------------------------------
    def _get_camera_key(self):
        if self.cap is None or not self.cap.isOpened():
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

    # ------------------------------------------------------------------
    # Cifrar Imagen
    # ------------------------------------------------------------------
    def encrypt_image(self):
        filepath = filedialog.askopenfilename(
            title="Selecciona una imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return
        self._cifrar_archivo_generico(filepath, tipo="imagen")

    # ------------------------------------------------------------------
    # Cifrar Documentos
    # ------------------------------------------------------------------
    def encrypt_document(self):
        filepath = filedialog.askopenfilename(title="Selecciona un documento")
        if not filepath:
            return
        self._cifrar_archivo_generico(filepath, tipo="documento")

    def _cifrar_archivo_generico(self, filepath, tipo):
        key = self._get_camera_key()
        if not key:
            return
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            token = Fernet(key).encrypt(data)
            with open(filepath, "wb") as f:
                f.write(token)

            key_str = key.decode()
            self.root.clipboard_clear()
            self.root.clipboard_append(key_str)
            self.root.update()

            key_filepath = filepath + ".key"
            with open(key_filepath, "w") as kf:
                kf.write(key_str)

            agregar_clave(tipo, filepath, key_str)

            messagebox.showinfo(
                "Éxito",
                f"{'Imagen' if tipo == 'imagen' else 'Documento'} cifrado.\n\n"
                f"La clave se copió al portapapeles, se guardó en '{os.path.basename(key_filepath)}' "
                "y quedó registrada en el panel de Descifrar."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cifrar: {e}")

    # ------------------------------------------------------------------
    # Cifrar Carpetas (cifra todos los archivos dentro, con UNA sola clave)
    # ------------------------------------------------------------------
    def encrypt_folder(self):
        folder = filedialog.askdirectory(title="Selecciona una carpeta")
        if not folder:
            return

        key = self._get_camera_key()
        if not key:
            return

        archivos_afectados = []
        errores = 0
        for carpeta_actual, _dirs, files in os.walk(folder):
            for fname in files:
                if fname.endswith(".key") or fname == "_carpeta.key":
                    continue
                fpath = os.path.join(carpeta_actual, fname)
                try:
                    with open(fpath, "rb") as f:
                        data = f.read()
                    token = Fernet(key).encrypt(data)
                    with open(fpath, "wb") as f:
                        f.write(token)
                    archivos_afectados.append(fpath)
                except Exception:
                    errores += 1

        key_str = key.decode()
        self.root.clipboard_clear()
        self.root.clipboard_append(key_str)
        self.root.update()

        try:
            with open(os.path.join(folder, "_carpeta.key"), "w") as kf:
                kf.write(key_str)
        except OSError:
            pass

        agregar_clave("carpeta", folder, key_str, archivos=archivos_afectados)

        msg = (
            f"Carpeta cifrada: {len(archivos_afectados)} archivo(s).\n\n"
            "La clave se copió al portapapeles y quedó registrada en el panel de Descifrar."
        )
        if errores:
            msg += f"\n\n({errores} archivo(s) no se pudieron cifrar)"
        messagebox.showinfo("Éxito", msg)


if __name__ == "__main__":
    import cv2
    root = tk.Tk()
    cap = cv2.VideoCapture(0)
    app = EreboApp(root, cap)
    root.mainloop()
