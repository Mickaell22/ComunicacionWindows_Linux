#!/usr/bin/env python3
"""
Script para compilar Clipboard Sync a un ejecutable .exe
"""

import os
import sys
import subprocess
from pathlib import Path

def create_icon():
    """Crea un ícono .ico para la aplicación"""
    print("Creando ícono para la aplicación...")
    try:
        from PIL import Image, ImageDraw

        # Crear una imagen de 256x256
        size = 256
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Dibujar un círculo azul con borde
        margin = 20
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill='#2196F3',
            outline='#1976D2',
            width=8
        )

        # Guardar como .ico
        icon_path = Path("clipboard_sync.ico")
        # Crear múltiples tamaños para el .ico
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        images = []
        for size_tuple in icon_sizes:
            img_resized = image.resize(size_tuple, Image.Resampling.LANCZOS)
            images.append(img_resized)

        images[0].save(
            str(icon_path),
            format='ICO',
            sizes=[img.size for img in images],
            append_images=images[1:]
        )

        print(f"[OK] Icono creado: {icon_path}")
        return str(icon_path)

    except Exception as e:
        print(f"[!] No se pudo crear el icono: {e}")
        print("  Continuando sin icono personalizado...")
        return None


def build_exe():
    """Compila la aplicación a un ejecutable"""
    print("=" * 60)
    print("  Compilando Clipboard Sync a .exe")
    print("=" * 60)
    print()

    # Verificar que PyInstaller este instalado
    try:
        import PyInstaller
        print(f"[OK] PyInstaller encontrado (version {PyInstaller.__version__})")
    except ImportError:
        print("[X] PyInstaller no esta instalado")
        print("  Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller instalado")

    # Crear ícono
    icon_path = create_icon()

    # Construir comando de PyInstaller
    cmd = [
        "pyinstaller",
        "--name=ClipboardSync",
        "--onefile",
        "--windowed",  # Sin consola
        "--clean",
    ]

    # Agregar ícono si existe
    if icon_path and os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")

    # Archivo principal
    cmd.append("clipboard_sync_gui.py")

    print()
    print("Ejecutando PyInstaller...")
    print(f"Comando: {' '.join(cmd)}")
    print()

    try:
        # Ejecutar PyInstaller
        result = subprocess.run(cmd, check=True)

        print()
        print("=" * 60)
        print("  [OK] Compilacion exitosa!")
        print("=" * 60)
        print()
        print(f"El archivo ejecutable se encuentra en:")
        print(f"  -> dist/ClipboardSync.exe")
        print()
        print("Puedes copiar este archivo a cualquier ubicacion y ejecutarlo.")
        print("No necesitaras Python instalado en la maquina donde lo uses.")
        print()

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("  [X] Error durante la compilacion")
        print("=" * 60)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
