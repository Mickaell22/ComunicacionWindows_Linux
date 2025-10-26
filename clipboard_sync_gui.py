#!/usr/bin/env python3
"""
Clipboard Sync GUI - Interfaz gráfica para sincronizador de portapapeles
Soporta Windows y Linux (Kali)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import time
import pyperclip
import json
import os
from datetime import datetime
import pystray
from PIL import Image, ImageDraw
from kvm_sync import KVMSync


class ClipboardSyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Clipboard Sync - Sincronizador de Portapapeles")
        self.root.geometry("650x700")
        self.root.resizable(False, False)

        # Archivo de configuración
        self.config_file = "clipboard_sync_config.json"

        # Variables
        self.running = False
        self.mode = tk.StringVar(value="server")
        self.host_var = tk.StringVar(value="")
        self.port_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Detenido")

        # Variables de sincronización
        self.last_clipboard = ""
        self.connections = []
        self.client_socket = None
        self.server_socket = None

        # System tray
        self.tray_icon = None
        self.is_hidden = False

        # KVM (Keyboard/Mouse sharing)
        self.kvm_enabled = tk.BooleanVar(value=False)
        self.kvm_sync = None
        self.control_status_var = tk.StringVar(value="Sin control")

        # Cargar configuración previa
        self.load_config()

        self.create_widgets()
        self.update_interface()

        # Configurar system tray
        self.setup_tray()

        # Configurar comportamiento de cierre/minimizar
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.root.bind("<Unmap>", self.on_minimize)

    def load_config(self):
        """Carga la configuración desde el archivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.mode.set(config.get('mode', 'server'))
                    self.host_var.set(config.get('host', ''))
                    self.port_var.set(config.get('port', ''))
        except Exception as e:
            print(f"Error cargando configuración: {e}")

    def save_config(self):
        """Guarda la configuración actual en el archivo JSON"""
        try:
            config = {
                'mode': self.mode.get(),
                'host': self.host_var.get(),
                'port': self.port_var.get()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error guardando configuración: {e}")

    def create_tray_icon(self):
        """Crea un ícono simple para el system tray"""
        # Crear una imagen de 64x64 con un círculo
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)

        # Dibujar un círculo azul con una "C" estilizada
        draw.ellipse([8, 8, 56, 56], fill='#2196F3', outline='#1976D2', width=2)

        # Dibujar texto "C" en el centro
        draw.text((22, 16), "C", fill='white')

        return image

    def setup_tray(self):
        """Configura el ícono del system tray"""
        icon_image = self.create_tray_icon()

        # Crear el menú del tray
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar", self.show_window, default=True),
            pystray.MenuItem("Ocultar", self.hide_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Estado", self.show_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", self.quit_app)
        )

        # Crear el ícono del tray
        self.tray_icon = pystray.Icon("clipboard_sync", icon_image, "Clipboard Sync", menu)

        # Ejecutar el tray en un hilo separado
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """Muestra la ventana principal"""
        self.is_hidden = False
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self, icon=None, item=None):
        """Oculta la ventana al system tray"""
        self.is_hidden = True
        self.root.withdraw()

    def on_minimize(self, event):
        """Se ejecuta cuando se minimiza la ventana"""
        if event.widget == self.root and self.root.state() == 'iconic':
            self.hide_window()

    def show_status(self, icon=None, item=None):
        """Muestra el estado actual en una notificación"""
        status = self.status_var.get()
        try:
            if self.tray_icon:
                self.tray_icon.notify(f"Estado: {status}", "Clipboard Sync")
        except:
            pass

    def quit_app(self, icon=None, item=None):
        """Cierra completamente la aplicación"""
        if self.running:
            response = messagebox.askokcancel(
                "Salir",
                "La sincronización está activa. ¿Deseas detenerla y salir?",
                parent=self.root if not self.is_hidden else None
            )
            if not response:
                return

        self.stop_sync()

        # Detener el tray icon
        if self.tray_icon:
            self.tray_icon.stop()

        self.root.quit()
        self.root.destroy()

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Título
        title_label = ttk.Label(main_frame, text="Clipboard Sync",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Modo de operación
        mode_frame = ttk.LabelFrame(main_frame, text="Modo de Operación", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Radiobutton(mode_frame, text="Servidor", variable=self.mode,
                       value="server", command=self.update_interface).grid(row=0, column=0, padx=20)
        ttk.Radiobutton(mode_frame, text="Cliente", variable=self.mode,
                       value="client", command=self.update_interface).grid(row=0, column=1, padx=20)

        # Configuración de red
        network_frame = ttk.LabelFrame(main_frame, text="Configuración de Red", padding="10")
        network_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Host
        ttk.Label(network_frame, text="IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.host_entry = ttk.Entry(network_frame, textvariable=self.host_var, width=30)
        self.host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Placeholder para IP
        if not self.host_var.get() and self.mode.get() == "client":
            self.host_entry.insert(0, "Ej: 192.168.1.100")
            self.host_entry.config(foreground='gray')

        def on_host_focus_in(event):
            if self.host_entry.get() == "Ej: 192.168.1.100":
                self.host_entry.delete(0, tk.END)
                self.host_entry.config(foreground='black')

        def on_host_focus_out(event):
            if not self.host_entry.get() and self.mode.get() == "client":
                self.host_entry.insert(0, "Ej: 192.168.1.100")
                self.host_entry.config(foreground='gray')

        self.host_entry.bind('<FocusIn>', on_host_focus_in)
        self.host_entry.bind('<FocusOut>', on_host_focus_out)

        # Puerto
        ttk.Label(network_frame, text="Puerto:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_entry = ttk.Entry(network_frame, textvariable=self.port_var, width=30)
        self.port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Placeholder para puerto
        if not self.port_var.get():
            self.port_entry.insert(0, "Ej: 5555")
            self.port_entry.config(foreground='gray')

        def on_port_focus_in(event):
            if self.port_entry.get() == "Ej: 5555":
                self.port_entry.delete(0, tk.END)
                self.port_entry.config(foreground='black')

        def on_port_focus_out(event):
            if not self.port_entry.get():
                self.port_entry.insert(0, "Ej: 5555")
                self.port_entry.config(foreground='gray')

        self.port_entry.bind('<FocusIn>', on_port_focus_in)
        self.port_entry.bind('<FocusOut>', on_port_focus_out)

        # Botón de IP local
        self.ip_button = ttk.Button(network_frame, text="Obtener IP Local",
                                    command=self.get_local_ip)
        self.ip_button.grid(row=0, column=2, padx=5)

        # Estado
        status_frame = ttk.LabelFrame(main_frame, text="Estado", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        # Opciones KVM
        kvm_frame = ttk.LabelFrame(main_frame, text="Compartir Mouse/Teclado (KVM)", padding="10")
        kvm_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.kvm_checkbox = ttk.Checkbutton(
            kvm_frame,
            text="Activar compartir mouse/teclado",
            variable=self.kvm_enabled,
            command=self.toggle_kvm
        )
        self.kvm_checkbox.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        # Estado de control KVM
        self.control_label = ttk.Label(
            kvm_frame,
            textvariable=self.control_status_var,
            font=("Arial", 9, "italic"),
            foreground="gray"
        )
        self.control_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)

        # Ayuda KVM
        kvm_help = ttk.Label(
            kvm_frame,
            text="Presiona Ctrl+Alt+Shift+S para cambiar el control entre dispositivos",
            font=("Arial", 8),
            foreground="blue"
        )
        kvm_help.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)

        # Controles
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=5, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(control_frame, text="Iniciar",
                                       command=self.start_sync, width=15)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Detener",
                                     command=self.stop_sync, width=15, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Registro de Actividad", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70,
                                                  state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar tags para colores
        self.log_text.tag_config("info", foreground="blue")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")

    def update_interface(self):
        """Actualiza la interfaz según el modo seleccionado"""
        if self.mode.get() == "server":
            self.host_entry.config(state=tk.DISABLED)
            self.ip_button.config(state=tk.NORMAL)
        else:
            self.host_entry.config(state=tk.NORMAL)
            self.ip_button.config(state=tk.DISABLED)

    def get_local_ip(self):
        """Obtiene la IP local del dispositivo"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.log(f"IP Local: {local_ip}", "success")
            messagebox.showinfo("IP Local", f"Tu IP local es:\n{local_ip}\n\nUsa esta IP para que el cliente se conecte.")
        except Exception as e:
            self.log(f"Error obteniendo IP: {e}", "error")

    def log(self, message, tag="info"):
        """Agrega un mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    # === FUNCIONES KVM ===

    def toggle_kvm(self):
        """Activa o desactiva KVM"""
        if not self.running:
            messagebox.showwarning(
                "Advertencia",
                "Debes iniciar la sincronizacion primero antes de activar KVM."
            )
            self.kvm_enabled.set(False)
            return

        if self.kvm_enabled.get():
            # Activar KVM
            self.start_kvm()
        else:
            # Desactivar KVM
            self.stop_kvm()

    def start_kvm(self):
        """Inicia el sistema KVM"""
        try:
            if self.kvm_sync is None:
                self.kvm_sync = KVMSync(
                    send_callback=self.send_kvm_event,
                    log_callback=self.log
                )

            self.kvm_sync.start()
            self.control_status_var.set("TIENES EL CONTROL (Ctrl+Alt+Shift+S para cambiar)")
            self.log("KVM activado - Compartiendo mouse/teclado", "success")
        except Exception as e:
            self.log(f"Error iniciando KVM: {e}", "error")
            self.kvm_enabled.set(False)

    def stop_kvm(self):
        """Detiene el sistema KVM"""
        if self.kvm_sync:
            self.kvm_sync.stop()
            self.control_status_var.set("Sin control")
            self.log("KVM desactivado", "info")

    def send_kvm_event(self, event_data):
        """Envia un evento KVM al dispositivo remoto"""
        try:
            # Crear un mensaje con protocolo
            message = {
                'protocol': 'kvm',
                'data': event_data
            }
            msg_json = json.dumps(message)
            msg_bytes = msg_json.encode('utf-8')
            msg_size = len(msg_bytes).to_bytes(4, byteorder='big')

            # Enviar segun el modo
            if self.mode.get() == "server":
                # Servidor: enviar a todos los clientes
                for conn in self.connections[:]:
                    try:
                        conn.sendall(msg_size + msg_bytes)
                    except:
                        pass
            else:
                # Cliente: enviar al servidor
                if self.client_socket:
                    try:
                        self.client_socket.sendall(msg_size + msg_bytes)
                    except:
                        pass
        except Exception as e:
            self.log(f"Error enviando evento KVM: {e}", "error")

    def handle_kvm_message(self, data):
        """Maneja un mensaje KVM recibido"""
        try:
            if self.kvm_sync and self.kvm_enabled.get():
                self.kvm_sync.handle_remote_event(data)
        except Exception as e:
            self.log(f"Error manejando mensaje KVM: {e}", "error")

    # === FIN FUNCIONES KVM ===

    def start_sync(self):
        """Inicia la sincronización"""
        # Validar puerto
        port_text = self.port_var.get()
        if not port_text or port_text == "Ej: 5555":
            messagebox.showerror("Error", "Debes ingresar un puerto.")
            return

        try:
            port = int(port_text)
            if port < 1 or port > 65535:
                raise ValueError("Puerto inválido")
        except ValueError:
            messagebox.showerror("Error", "Puerto inválido. Debe ser un número entre 1 y 65535.")
            return

        # Validar IP en modo cliente
        host_text = self.host_var.get()
        if self.mode.get() == "client":
            if not host_text or host_text == "Ej: 192.168.1.100":
                messagebox.showerror("Error", "Debes ingresar la IP del servidor.")
                return

        # Guardar configuración
        self.save_config()

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Iniciar en hilo separado
        if self.mode.get() == "server":
            threading.Thread(target=self.run_server, daemon=True).start()
        else:
            threading.Thread(target=self.run_client, daemon=True).start()

    def stop_sync(self):
        """Detiene la sincronización"""
        self.running = False
        self.status_var.set("Deteniendo...")
        self.log("Deteniendo sincronización...", "warning")

        # Detener KVM si está activo
        if self.kvm_enabled.get():
            self.stop_kvm()
            self.kvm_enabled.set(False)

        # Cerrar conexiones
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass

        for conn in self.connections[:]:
            try:
                conn.close()
            except:
                pass
        self.connections.clear()

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Detenido")
        self.log("Sincronización detenida", "info")

    def monitor_clipboard(self, send_callback):
        """Monitorea cambios en el portapapeles"""
        self.log("Monitoreando portapapeles...", "info")
        while self.running:
            try:
                current_clipboard = pyperclip.paste()

                if current_clipboard != self.last_clipboard and current_clipboard:
                    self.log(f"Nuevo contenido detectado ({len(current_clipboard)} caracteres)", "success")
                    self.last_clipboard = current_clipboard
                    send_callback(current_clipboard)

                time.sleep(0.5)
            except Exception as e:
                if self.running:
                    self.log(f"Error monitoreando portapapeles: {e}", "error")
                time.sleep(1)

    def update_clipboard(self, content):
        """Actualiza el portapapeles local"""
        try:
            if content != self.last_clipboard:
                pyperclip.copy(content)
                self.last_clipboard = content
                self.log(f"Portapapeles actualizado ({len(content)} caracteres)", "success")
        except Exception as e:
            self.log(f"Error actualizando portapapeles: {e}", "error")

    def handle_client(self, conn, addr):
        """Maneja la conexión de un cliente"""
        self.log(f"Cliente conectado desde {addr[0]}:{addr[1]}", "success")
        self.connections.append(conn)
        self.status_var.set(f"Servidor activo - {len(self.connections)} cliente(s)")

        try:
            while self.running:
                size_data = conn.recv(4)
                if not size_data:
                    break

                msg_size = int.from_bytes(size_data, byteorder='big')

                data = b''
                while len(data) < msg_size:
                    packet = conn.recv(min(msg_size - len(data), 4096))
                    if not packet:
                        break
                    data += packet

                if data:
                    content = data.decode('utf-8', errors='ignore')

                    # Detectar tipo de mensaje
                    try:
                        message = json.loads(content)
                        if isinstance(message, dict) and 'protocol' in message:
                            # Mensaje con protocolo
                            if message['protocol'] == 'kvm':
                                self.handle_kvm_message(message['data'])
                            elif message['protocol'] == 'clipboard':
                                self.update_clipboard(message['data'])
                        else:
                            # Mensaje legacy (clipboard)
                            self.update_clipboard(content)
                    except json.JSONDecodeError:
                        # No es JSON, asumir clipboard legacy
                        self.update_clipboard(content)

        except Exception as e:
            if self.running:
                self.log(f"Error con cliente {addr}: {e}", "error")
        finally:
            if conn in self.connections:
                self.connections.remove(conn)
            conn.close()
            self.log(f"Cliente {addr[0]}:{addr[1]} desconectado", "warning")
            self.status_var.set(f"Servidor activo - {len(self.connections)} cliente(s)")

    def broadcast_to_clients(self, content):
        """Envía contenido de clipboard a todos los clientes conectados"""
        # Usar el nuevo protocolo
        message = {
            'protocol': 'clipboard',
            'data': content
        }
        msg = json.dumps(message).encode('utf-8')
        msg_size = len(msg).to_bytes(4, byteorder='big')

        for conn in self.connections[:]:
            try:
                conn.sendall(msg_size + msg)
            except Exception as e:
                self.log(f"Error enviando a cliente: {e}", "error")
                if conn in self.connections:
                    self.connections.remove(conn)
                conn.close()

    def run_server(self):
        """Ejecuta el modo servidor"""
        try:
            port = int(self.port_var.get())
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", port))
            self.server_socket.listen(5)

            self.log(f"Servidor escuchando en puerto {port}", "success")
            self.status_var.set(f"Servidor activo - 0 clientes")

            # Mostrar IP local
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                self.log(f"IP local: {local_ip}", "success")
            except:
                pass

            # Iniciar monitoreo del portapapeles
            clipboard_thread = threading.Thread(
                target=self.monitor_clipboard,
                args=(self.broadcast_to_clients,),
                daemon=True
            )
            clipboard_thread.start()

            # Aceptar conexiones
            while self.running:
                self.server_socket.settimeout(1.0)
                try:
                    conn, addr = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except OSError:
                    break

        except Exception as e:
            self.log(f"Error del servidor: {e}", "error")
            self.status_var.set("Error")
        finally:
            if self.running:
                self.stop_sync()

    def send_to_server(self, content):
        """Envía contenido de clipboard al servidor"""
        if self.client_socket:
            try:
                # Usar el nuevo protocolo
                message = {
                    'protocol': 'clipboard',
                    'data': content
                }
                msg = json.dumps(message).encode('utf-8')
                msg_size = len(msg).to_bytes(4, byteorder='big')
                self.client_socket.sendall(msg_size + msg)
            except Exception as e:
                self.log(f"Error enviando al servidor: {e}", "error")

    def receive_from_server(self):
        """Recibe contenido del servidor"""
        try:
            while self.running:
                size_data = self.client_socket.recv(4)
                if not size_data:
                    break

                msg_size = int.from_bytes(size_data, byteorder='big')

                data = b''
                while len(data) < msg_size:
                    packet = self.client_socket.recv(min(msg_size - len(data), 4096))
                    if not packet:
                        break
                    data += packet

                if data:
                    content = data.decode('utf-8', errors='ignore')

                    # Detectar tipo de mensaje
                    try:
                        message = json.loads(content)
                        if isinstance(message, dict) and 'protocol' in message:
                            # Mensaje con protocolo
                            if message['protocol'] == 'kvm':
                                self.handle_kvm_message(message['data'])
                            elif message['protocol'] == 'clipboard':
                                self.update_clipboard(message['data'])
                        else:
                            # Mensaje legacy (clipboard)
                            self.update_clipboard(content)
                    except json.JSONDecodeError:
                        # No es JSON, asumir clipboard legacy
                        self.update_clipboard(content)

        except Exception as e:
            if self.running:
                self.log(f"Error recibiendo del servidor: {e}", "error")
        finally:
            if self.running:
                self.log("Conexión con servidor cerrada", "warning")
                self.status_var.set("Desconectado")

    def run_client(self):
        """Ejecuta el modo cliente"""
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())

            self.log(f"Conectando a {host}:{port}...", "info")
            self.status_var.set("Conectando...")

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))

            self.log("Conectado al servidor", "success")
            self.status_var.set("Conectado")

            # Iniciar hilo para recibir del servidor
            receive_thread = threading.Thread(target=self.receive_from_server, daemon=True)
            receive_thread.start()

            # Iniciar monitoreo del portapapeles
            clipboard_thread = threading.Thread(
                target=self.monitor_clipboard,
                args=(self.send_to_server,),
                daemon=True
            )
            clipboard_thread.start()

            # Mantener el programa corriendo
            while self.running:
                time.sleep(1)

        except Exception as e:
            self.log(f"Error de conexión: {e}", "error")
            self.status_var.set("Error de conexión")
        finally:
            if self.running:
                self.stop_sync()


def main():
    root = tk.Tk()
    app = ClipboardSyncGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
