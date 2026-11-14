import os
import platform
import shutil
import subprocess
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import speech_recognition as sr

# ================= CONFIGURACIÓN (desde .env) =================
load_dotenv(Path(__file__).resolve().parent / ".env")

RUTA_ARCHIVO = Path(os.environ["RUTA_ARCHIVO"])
REPO_PATH = Path(os.environ["REPO_PATH"])
IDIOMA = os.environ.get("IDIOMA", "es-PE")


def normalizar(texto):
    """Quita tildes y pasa a minúsculas."""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower().strip()


FRASES_ACTIVACION = [
    normalizar(f)
    for f in os.environ["FRASES_ACTIVACION"].split(";")
    if f.strip()
]
# ==============================================================


def frase_detectada(texto):
    return any(frase in texto for frase in FRASES_ACTIVACION)


def abrir_y_esperar(ruta):
    """Abre el archivo y espera a que cierres el editor."""
    ruta = str(ruta)
    if not os.path.exists(ruta):
        print("❌ No se encontró el archivo:", ruta)
        return False

    sistema = platform.system()
    if sistema == "Windows":
        subprocess.run(["notepad", ruta])
    elif sistema == "Darwin":
        subprocess.run(["open", "-W", "-t", ruta])
    else:
        for editor in ["gedit", "mousepad", "kate", "xed", "pluma"]:
            if shutil.which(editor):
                subprocess.run([editor, "--wait", ruta])
                break
        else:
            print("ℹ️  No hay editor gráfico. Se abrirá nano en una terminal.")
            subprocess.run(["x-terminal-emulator", "-e", "nano", ruta])

    print("📝 Editor cerrado.")
    return True


def git(*args):
    resultado = subprocess.run(
        ["git", *args],
        cwd=str(REPO_PATH),
        capture_output=True,
        text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr or resultado.stdout)
    return resultado.stdout


def subir_cambios():
    """Revisa cambios; si los hay, hace add, commit y push."""
    try:
        if not git("status", "--porcelain").strip():
            print("ℹ️  No hay cambios. No se hace commit ni push.")
            return

        print("⏳ git add .")
        git("add", ".")

        mensaje = "Actualización " + datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f'⏳ git commit -m "{mensaje}"')
        git("commit", "-m", mensaje)

        print("⏳ git push")
        git("push")

        print("✅ Commit y push realizados correctamente.")
    except (RuntimeError, OSError) as e:
        print("❌ Error de git:\n", e)


def escuchar():
    reconocedor = sr.Recognizer()
    reconocedor.dynamic_energy_threshold = True
    reconocedor.energy_threshold = 300
    reconocedor.pause_threshold = 0.5
    reconocedor.non_speaking_duration = 0.3

    with sr.Microphone() as microfono:
        print("Calibrando ruido ambiente (2 s)...")
        reconocedor.adjust_for_ambient_noise(microfono, duration=2)
        print("🎙️  Escuchando... di una de las frases de activación")

        while True:
            try:
                audio = reconocedor.listen(microfono, timeout=3, phrase_time_limit=4)
                texto = normalizar(reconocedor.recognize_google(audio, language=IDIOMA))
                print("Escuché:", texto)

                if frase_detectada(texto):
                    if abrir_y_esperar(RUTA_ARCHIVO):
                        subir_cambios()
                    print("🎙️  Volviendo a escuchar...")

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print("Error del servicio de voz (¿sin internet?):", e)
                time.sleep(3)


if __name__ == "__main__":
    try:
        escuchar()
    except KeyboardInterrupt:
        print("\nJarvis desactivado.")