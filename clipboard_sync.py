#!/usr/bin/env python3
"""
Clipboard Sync - Sincronizador de portapapeles entre dispositivos
Soporta Windows y Linux (Kali)
"""

import socket
import threading
import time
import sys
import pyperclip
import argparse

class ClipboardSync:
    def __init__(self, mode, host='0.0.0.0', port=5555):
        self.mode = mode
        self.host = host
        self.port = port
        self.last_clipboard = ""
        self.running = True
        self.connections = []

    def monitor_clipboard(self, send_callback):
        """Monitorea cambios en el portapapeles y los envía"""
        print("[*] Monitoreando portapapeles...")
        while self.running:
            try:
                current_clipboard = pyperclip.paste()

                # Si hay un cambio en el portapapeles
                if current_clipboard != self.last_clipboard and current_clipboard:
                    print(f"[+] Nuevo contenido detectado ({len(current_clipboard)} caracteres)")
                    self.last_clipboard = current_clipboard
                    send_callback(current_clipboard)

                time.sleep(0.5)  # Revisar cada 0.5 segundos

            except Exception as e:
                print(f"[!] Error monitoreando portapapeles: {e}")
                time.sleep(1)

    def update_clipboard(self, content):
        """Actualiza el portapapeles local"""
        try:
            if content != self.last_clipboard:
                pyperclip.copy(content)
                self.last_clipboard = content
                print(f"[+] Portapapeles actualizado ({len(content)} caracteres)")
        except Exception as e:
            print(f"[!] Error actualizando portapapeles: {e}")

    def handle_client(self, conn, addr):
        """Maneja la conexión de un cliente"""
        print(f"[+] Cliente conectado desde {addr}")
        self.connections.append(conn)

        try:
            while self.running:
                # Recibir tamaño del mensaje
                size_data = conn.recv(4)
                if not size_data:
                    break

                msg_size = int.from_bytes(size_data, byteorder='big')

                # Recibir el contenido
                data = b''
                while len(data) < msg_size:
                    packet = conn.recv(min(msg_size - len(data), 4096))
                    if not packet:
                        break
                    data += packet

                if data:
                    content = data.decode('utf-8', errors='ignore')
                    self.update_clipboard(content)

        except Exception as e:
            print(f"[!] Error con cliente {addr}: {e}")
        finally:
            if conn in self.connections:
                self.connections.remove(conn)
            conn.close()
            print(f"[-] Cliente {addr} desconectado")

    def broadcast_to_clients(self, content):
        """Envía contenido a todos los clientes conectados"""
        msg = content.encode('utf-8')
        msg_size = len(msg).to_bytes(4, byteorder='big')

        for conn in self.connections[:]:  # Copia de la lista
            try:
                conn.sendall(msg_size + msg)
            except Exception as e:
                print(f"[!] Error enviando a cliente: {e}")
                if conn in self.connections:
                    self.connections.remove(conn)
                conn.close()

    def run_server(self):
        """Ejecuta el modo servidor"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)

        print(f"[*] Servidor escuchando en {self.host}:{self.port}")
        print(f"[*] Los clientes deben conectarse a esta IP")

        # Obtener y mostrar la IP local
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"[*] IP local: {local_ip}")
        except:
            pass

        # Iniciar monitoreo del portapapeles
        clipboard_thread = threading.Thread(
            target=self.monitor_clipboard,
            args=(self.broadcast_to_clients,)
        )
        clipboard_thread.daemon = True
        clipboard_thread.start()

        # Aceptar conexiones
        try:
            while self.running:
                server.settimeout(1.0)
                try:
                    conn, addr = server.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue

        except KeyboardInterrupt:
            print("\n[*] Deteniendo servidor...")
        finally:
            self.running = False
            for conn in self.connections:
                conn.close()
            server.close()

    def send_to_server(self, content):
        """Envía contenido al servidor"""
        if hasattr(self, 'client_socket') and self.client_socket:
            try:
                msg = content.encode('utf-8')
                msg_size = len(msg).to_bytes(4, byteorder='big')
                self.client_socket.sendall(msg_size + msg)
            except Exception as e:
                print(f"[!] Error enviando al servidor: {e}")

    def receive_from_server(self):
        """Recibe contenido del servidor"""
        try:
            while self.running:
                # Recibir tamaño del mensaje
                size_data = self.client_socket.recv(4)
                if not size_data:
                    break

                msg_size = int.from_bytes(size_data, byteorder='big')

                # Recibir el contenido
                data = b''
                while len(data) < msg_size:
                    packet = self.client_socket.recv(min(msg_size - len(data), 4096))
                    if not packet:
                        break
                    data += packet

                if data:
                    content = data.decode('utf-8', errors='ignore')
                    self.update_clipboard(content)

        except Exception as e:
            print(f"[!] Error recibiendo del servidor: {e}")
        finally:
            print("[*] Conexión con servidor cerrada")

    def run_client(self):
        """Ejecuta el modo cliente"""
        print(f"[*] Conectando a {self.host}:{self.port}...")

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client_socket.connect((self.host, self.port))
            print("[+] Conectado al servidor")

            # Iniciar hilo para recibir del servidor
            receive_thread = threading.Thread(target=self.receive_from_server)
            receive_thread.daemon = True
            receive_thread.start()

            # Iniciar monitoreo del portapapeles
            clipboard_thread = threading.Thread(
                target=self.monitor_clipboard,
                args=(self.send_to_server,)
            )
            clipboard_thread.daemon = True
            clipboard_thread.start()

            # Mantener el programa corriendo
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[*] Deteniendo cliente...")

        except Exception as e:
            print(f"[!] Error de conexión: {e}")
        finally:
            self.running = False
            self.client_socket.close()

def main():
    parser = argparse.ArgumentParser(
        description='Clipboard Sync - Sincronizador de portapapeles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  Modo servidor:
    python clipboard_sync.py server
    python clipboard_sync.py server --port 6000

  Modo cliente:
    python clipboard_sync.py client --host 192.168.1.100
    python clipboard_sync.py client --host 192.168.1.100 --port 6000
        """
    )

    parser.add_argument('mode', choices=['server', 'client'],
                       help='Modo de operación: server o client')
    parser.add_argument('--host', default='0.0.0.0',
                       help='IP del servidor (para cliente) o interfaz (para servidor)')
    parser.add_argument('--port', type=int, default=5555,
                       help='Puerto a usar (default: 5555)')

    args = parser.parse_args()

    print("=" * 60)
    print("  Clipboard Sync - Sincronizador de Portapapeles")
    print("=" * 60)
    print()

    sync = ClipboardSync(args.mode, args.host, args.port)

    if args.mode == 'server':
        sync.run_server()
    else:
        sync.run_client()

if __name__ == "__main__":
    main()
