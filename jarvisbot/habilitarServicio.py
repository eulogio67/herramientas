import os
import subprocess
import sys
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
GITIGNORE_PATH = BASE_DIR / ".gitignore"
INDEX_PATH = BASE_DIR / "index.py"
VENV_PYTHON = Path(sys.executable)
SERVICE_DIR = Path.home() / ".config" / "systemd" / "user"
SERVICE_NAME = "jarvisbot.service"
SERVICE_PATH = SERVICE_DIR / SERVICE_NAME

FRASES_DEFAULT = "jarvis abre uea;jarvis abre wea;jarvis abre abreu;jarvis abreu"


def comprobar_requisitos():
    if not INDEX_PATH.exists():
        sys.exit(f"❌ No existe {INDEX_PATH}")

    faltantes = []
    for modulo in ["speech_recognition", "pyaudio", "dotenv"]:
        resultado = subprocess.run(
            [sys.executable, "-c", f"import {modulo}"],
            capture_output=True,
        )
        if resultado.returncode != 0:
            faltantes.append(modulo)

    if faltantes:
        sys.exit(
            "❌ Faltan librerías en este Python: " + ", ".join(faltantes) + "\n"
            f"   Instálalas con: {sys.executable} -m pip install SpeechRecognition pyaudio python-dotenv"
        )
    print(f"✅ Usando Python: {sys.executable}")

def seleccionar_uea_txt():
    root = tk.Tk()
    root.withdraw()
    ruta = filedialog.askopenfilename(
        title="Selecciona UEA.txt",
        initialdir=str(Path.home()),
        filetypes=[("Archivo de texto", "*.txt")],
    )
    root.destroy()

    if not ruta:
        sys.exit("Operación cancelada.")

    ruta = Path(ruta).resolve()
    if ruta.name != "UEA.txt":
        messagebox_error = f"El archivo debe llamarse exactamente UEA.txt (seleccionaste: {ruta.name})"
        sys.exit("❌ " + messagebox_error)

    return ruta


def escribir_env(ruta_uea):
    contenido = (
        f'RUTA_ARCHIVO="{ruta_uea}"\n'
        f'REPO_PATH="{ruta_uea.parent}"\n'
        f'IDIOMA="es-PE"\n'
        f'FRASES_ACTIVACION="{FRASES_DEFAULT}"\n'
    )
    ENV_PATH.write_text(contenido, encoding="utf-8")
    print(f"✅ .env generado en {ENV_PATH}")

def agregar_env_a_gitignore():
    lineas = GITIGNORE_PATH.read_text(encoding="utf-8").splitlines() if GITIGNORE_PATH.exists() else []
    for entrada in [".env", ".venv/"]:
        if entrada not in lineas:
            lineas.append(entrada)
    GITIGNORE_PATH.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("✅ .env y .venv/ agregados a .gitignore")


def escribir_servicio():
    SERVICE_DIR.mkdir(parents=True, exist_ok=True)
    uid = os.getuid()
    display = os.environ.get("DISPLAY", ":0")
    wayland = os.environ.get("WAYLAND_DISPLAY", "wayland-0")

    contenido = f"""[Unit]
Description=JarvisBot
After=graphical-session.target sound.target

[Service]
ExecStart={VENV_PYTHON} {INDEX_PATH}
WorkingDirectory={BASE_DIR}
Environment=DISPLAY={display}
Environment=WAYLAND_DISPLAY={wayland}
Environment=XDG_RUNTIME_DIR=/run/user/{uid}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""
    SERVICE_PATH.write_text(contenido, encoding="utf-8")
    print(f"✅ Servicio generado en {SERVICE_PATH}")


def systemctl(*args):
    subprocess.run(["systemctl", "--user", *args], check=True)


def activar_servicio():
    systemctl("daemon-reload")
    systemctl("enable", SERVICE_NAME)
    systemctl("restart", SERVICE_NAME)
    print("✅ Servicio activado y reiniciado")
    subprocess.run(["systemctl", "--user", "status", SERVICE_NAME, "--no-pager"])


def main():
    comprobar_requisitos()
    ruta_uea = seleccionar_uea_txt()
    print(f"Archivo seleccionado: {ruta_uea}")
    escribir_env(ruta_uea)
    agregar_env_a_gitignore()
    escribir_servicio()
    activar_servicio()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("❌ Error al ejecutar systemctl:", e)