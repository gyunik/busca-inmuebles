import subprocess
import re
import sys
import os
import time
import socket
import webbrowser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0

def main():
    print("=" * 65)
    print("      BUSCA INMUEBLES - ACCESO WEB PUBLICO (HTTPS)")
    print("=" * 65)
    print()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    server_process = None

    # 1. Verificar si el servidor local ya esta corriendo
    if not is_port_open("127.0.0.1", 8000):
        print("[1/2] Iniciando servidor local FastAPI...")
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=base_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
    else:
        print("[1/2] Servidor local FastAPI ya esta activo en http://127.0.0.1:8000")

    cloudflared_bin = os.path.join(base_dir, "cloudflared.exe")
    if not os.path.exists(cloudflared_bin):
        print("[ERROR] No se encontro cloudflared.exe en:", cloudflared_bin)
        input("\nPresiona Enter para salir...")
        return

    # 2. Iniciar tunel de Cloudflare
    print("[2/2] Generando enlace seguro HTTPS en Cloudflare...")
    tunnel_cmd = [cloudflared_bin, "tunnel", "--url", "http://127.0.0.1:8000"]
    tunnel_process = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    url_found = None
    start_time = time.time()

    # Leer salida de cloudflared donde publica la URL
    for line in iter(tunnel_process.stdout.readline, ""):
        match = re.search(r'(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)', line)
        if match:
            url_found = match.group(1)
            break
        if time.time() - start_time > 20:
            break

    if url_found:
        # Guardar en archivo para facil acceso
        url_file = os.path.join(base_dir, "URL_ACCESO_WEB.txt")
        with open(url_file, "w", encoding="utf-8") as f:
            f.write(f"URL de Acceso Web Publico:\n{url_found}\n\nGenerado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        print()
        print("*" * 65)
        print("  TU SITIO WEB YA ESTA ONLINE Y ACCESIBLE DESDE CUALQUIER LUGAR!")
        print("*" * 65)
        print()
        print("  ENLACE SEGURO (HTTPS):")
        print(f"  >>>  {url_found}  <<<")
        print()
        print("  (Tambien guardado en el archivo URL_ACCESO_WEB.txt)")
        print("*" * 65)
        print()
        print("  Para mantener el sitio accesible, deja esta ventana abierta.")
        print("  Para cerrar el acceso web, presiona Ctrl + C o cierra esta ventana.")
        print("=" * 65)

        try:
            webbrowser.open(url_found)
        except Exception:
            pass

        try:
            for line in iter(tunnel_process.stdout.readline, ""):
                pass
        except KeyboardInterrupt:
            print("\nCerrando tunel web...")
            tunnel_process.terminate()
            if server_process:
                server_process.terminate()
    else:
        print("[AVISO] No se pudo obtener la URL automatica dentro del tiempo limite.")
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
