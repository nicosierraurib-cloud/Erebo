# Erebo

Erebo es un sistema de cifrado que funciona usando el sensor de tu camara mientras esta tapada, dentro de la app el script captura el ruido térmico de los electrones que pasan por el sensor en completa oscuridad y lo transforma en claves criptográficas para cifrar archivos de forma segura mediante SHA-256.

## Instalación Linux

Para evitar problemas con los entornos virtuales, instala las dependencias gráficas y de criptografía directamente desde los repositorios oficiales de pacman:

```bash
sudo pacman -S python-opencv python-cryptography tk
```
Nota: 
Tapa completamente la lente de tu cámara web. Si dejas entrar luz, el sistema usará patrones estructurados en lugar de ruido térmico, lo que debilita severamente la clave generada.

Ejecuta la interfaz gráfica:

```bash
python erebo_app.py
```
Puedes introducir texto o seleccionar un archivo de tu sistema.

Al hacer clic en "Cifrar", Érebo leerá el sensor y te entregará una clave alfanumérica en pantalla.

Guarda esa clave en un lugar seguro. La necesitarás obligatoriamente para descifrar el texto o recuperar el archivo.

Pdt: No se permite copiar el texto ni hacer captura de pantalla por seguridad, si en comentarios lo piden puedo hacer que genere un archivo en tu computadora con la clave.
