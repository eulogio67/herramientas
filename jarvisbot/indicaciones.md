# JarvisBot: instalación y arranque automático

Este proceso instala JarvisBot, te pide la ubicación de `UEA.txt` mediante una ventana y deja el bot corriendo como servicio que arranca con la sesión.

---

## Requisitos

- Linux (Pop!_OS o Ubuntu)
- Micrófono funcionando
- Acceso a GitHub configurado en la laptop (credenciales o llave SSH)
- Tu archivo `UEA.txt` dentro de la carpeta del repositorio de UEA, que debe tener `origin` configurado

---

## Paso 1: Clonar el repositorio

```bash
cd ~/Escritorio/herramientas
git clone https://github.com/TU_USUARIO/jarvisbot.git
cd jarvisbot
```

---

## Paso 2: Instalar dependencias

Dependencias del sistema (incluye `tkinter` para la ventana de selección y `portaudio` para `pyaudio`):

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-tk portaudio19-dev gedit
```

Entorno virtual fuera del proyecto, para que `git add .` no suba las librerías:

```bash
mkdir -p ~/.venvs
python3 -m venv ~/.venvs/jarvisbot
~/.venvs/jarvisbot/bin/pip install --upgrade pip
~/.venvs/jarvisbot/bin/pip install SpeechRecognition pyaudio python-dotenv
```

Verifica que todo esté bien:

```bash
~/.venvs/jarvisbot/bin/python -c "import speech_recognition, pyaudio, dotenv; print('OK')"
```

Debe imprimir `OK`.

---

## Paso 3: Ejecutar el configurador

```bash
cd ~/Escritorio/herramientas/jarvisbot
python3 habilitarServicio.py
```

El script hace lo siguiente:

1. Abre una ventana para que selecciones tu archivo **UEA.txt**. Si el archivo no se llama exactamente `UEA.txt`, se cancela.
2. Genera el archivo `.env` con la ruta del archivo, la carpeta del repositorio y las frases de activación.
3. Crea el servicio de usuario `jarvisbot.service` en `~/.config/systemd/user/`.
4. Ejecuta `daemon-reload`, activa el servicio para que arranque con la sesión y lo reinicia.

Al terminar debe mostrar `Active: active (running)`.

---

## Paso 4: Verificar

```bash
systemctl --user status jarvisbot.service
```

Para ver los mensajes en vivo:

```bash
journalctl --user -u jarvisbot.service -f
```

Sal con `Ctrl+C`. Luego di **"jarvis abre uea"** (o cualquiera de las frases configuradas). Se abrirá `UEA.txt`. Edita, guarda con `Ctrl+S` y cierra el editor. Si hubo cambios, el bot hace `git add .`, `git commit` y `git push`.

---

## Cambiar la ubicación de UEA.txt o las frases

Vuelve a ejecutar:

```bash
python3 habilitarServicio.py
```

El script sobrescribe el `.env` y reinicia el servicio. Las frases se pueden editar directamente en `.env`, en la variable `FRASES_ACTIVACION`, separadas por `;`. Después reinicia el servicio:

```bash
systemctl --user restart jarvisbot.service
```

---

## Comandos útiles

| Acción | Comando |
|---|---|
| Ver estado | `systemctl --user status jarvisbot.service` |
| Detener | `systemctl --user stop jarvisbot.service` |
| Iniciar | `systemctl --user start jarvisbot.service` |
| Reiniciar | `systemctl --user restart jarvisbot.service` |
| Desactivar arranque automático | `systemctl --user disable jarvisbot.service` |
| Ver logs | `journalctl --user -u jarvisbot.service -f` |

---

## Problemas comunes

**La ventana de selección no aparece**
Confirma que instalaste `python3-tk` (`sudo apt install python3-tk`).

**El editor no abre desde el servicio**
Revisa que `DISPLAY` esté en el servicio: `grep DISPLAY ~/.config/systemd/user/jarvisbot.service`. Si estás en Wayland, ejecuta `habilitarServicio.py` desde la sesión gráfica normal.

**El micrófono no responde al arrancar**
Espera unos segundos después de iniciar sesión y reinicia el servicio. Si persiste, agrega `ExecStartPre=/bin/sleep 10` en la sección `[Service]` del archivo `~/.config/systemd/user/jarvisbot.service`.

**`git push` pide contraseña**
El servicio no puede escribir credenciales. Configura una llave SSH o un token guardado con `git config --global credential.helper store` y haz un `git push` manual una vez.

**El servicio se cae**
Revisa el error con `journalctl --user -u jarvisbot.service -n 50`.

---

## Seguridad

- `.env` y `UEA.txt` contienen rutas y contraseñas. El configurador agrega `.env` al `.gitignore`.
- `UEA.txt` se sube en cada commit. Mantén el repositorio de UEA privado y con acceso solo para quien deba tenerlo.