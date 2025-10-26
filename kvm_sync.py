#!/usr/bin/env python3
"""
KVM Sync - Modulo para compartir mouse y teclado entre dispositivos
"""

import json
import threading
import time
from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key


class KVMSync:
    def __init__(self, send_callback, log_callback=None):
        """
        Inicializa el sincronizador de mouse/teclado

        Args:
            send_callback: Funcion para enviar eventos al dispositivo remoto
            log_callback: Funcion opcional para logging
        """
        self.send_callback = send_callback
        self.log_callback = log_callback

        # Estado
        self.enabled = False
        self.controlling = True  # True = este dispositivo controla, False = dispositivo remoto controla

        # Controladores para reproducir eventos
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()

        # Listeners para capturar eventos
        self.mouse_listener = None
        self.keyboard_listener = None
        self.hotkey_listener = None

        # Hotkey para cambiar control (Ctrl+Alt+Shift+S)
        self.hotkey_combination = {Key.ctrl_l, Key.alt_l, Key.shift, keyboard.KeyCode.from_char('s')}
        self.current_keys = set()

        # Evitar loops infinitos
        self.block_events = False

    def log(self, message, level="info"):
        """Helper para logging"""
        if self.log_callback:
            self.log_callback(message, level)

    def start(self):
        """Inicia la captura de eventos"""
        if self.enabled:
            return

        self.enabled = True
        self.controlling = True

        # Iniciar listener de mouse
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        self.mouse_listener.start()

        # Iniciar listener de teclado
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()

        # Iniciar listener de hotkey
        self.hotkey_listener = keyboard.Listener(
            on_press=self.on_hotkey_press,
            on_release=self.on_hotkey_release
        )
        self.hotkey_listener.start()

        self.log("KVM iniciado - Tienes el control (Ctrl+Alt+Shift+S para cambiar)", "success")

    def stop(self):
        """Detiene la captura de eventos"""
        if not self.enabled:
            return

        self.enabled = False

        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.hotkey_listener:
            self.hotkey_listener.stop()

        self.log("KVM detenido", "info")

    def toggle_control(self):
        """Cambia el control entre este dispositivo y el remoto"""
        self.controlling = not self.controlling

        if self.controlling:
            self.log("Ahora TIENES el control del mouse/teclado", "success")
        else:
            self.log("Control transferido al dispositivo REMOTO", "warning")

        # Notificar al otro dispositivo
        self.send_event({
            'type': 'control_change',
            'controlling': not self.controlling  # El otro dispositivo recibe el estado opuesto
        })

    # === CAPTURA DE EVENTOS ===

    def on_mouse_move(self, x, y):
        """Captura movimiento del mouse"""
        if not self.enabled or not self.controlling or self.block_events:
            return

        # Obtener tamaño de pantalla para coordenadas relativas
        from tkinter import Tk
        try:
            root = Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()

            # Convertir a coordenadas relativas (0-1)
            rel_x = x / screen_width
            rel_y = y / screen_height

            self.send_event({
                'type': 'mouse_move',
                'x': rel_x,
                'y': rel_y
            })
        except:
            pass

    def on_mouse_click(self, x, y, button, pressed):
        """Captura clicks del mouse"""
        if not self.enabled or not self.controlling or self.block_events:
            return

        button_name = button.name if hasattr(button, 'name') else str(button)

        self.send_event({
            'type': 'mouse_click',
            'button': button_name,
            'pressed': pressed
        })

    def on_mouse_scroll(self, x, y, dx, dy):
        """Captura scroll del mouse"""
        if not self.enabled or not self.controlling or self.block_events:
            return

        self.send_event({
            'type': 'mouse_scroll',
            'dx': dx,
            'dy': dy
        })

    def on_key_press(self, key):
        """Captura teclas presionadas"""
        if not self.enabled or not self.controlling or self.block_events:
            return

        key_data = self.serialize_key(key)
        if key_data:
            self.send_event({
                'type': 'key_press',
                'key': key_data
            })

    def on_key_release(self, key):
        """Captura teclas liberadas"""
        if not self.enabled or not self.controlling or self.block_events:
            return

        key_data = self.serialize_key(key)
        if key_data:
            self.send_event({
                'type': 'key_release',
                'key': key_data
            })

    # === HOTKEY PARA CAMBIAR CONTROL ===

    def on_hotkey_press(self, key):
        """Detecta hotkey para cambiar control"""
        try:
            self.current_keys.add(key)
        except:
            pass

        # Verificar si se presiono la combinacion completa
        if self.hotkey_combination.issubset(self.current_keys):
            self.toggle_control()

    def on_hotkey_release(self, key):
        """Limpia las teclas al soltar"""
        try:
            self.current_keys.discard(key)
        except:
            pass

    # === REPRODUCCION DE EVENTOS ===

    def handle_remote_event(self, event_data):
        """Maneja un evento recibido del dispositivo remoto"""
        if not self.enabled:
            return

        try:
            event = json.loads(event_data) if isinstance(event_data, str) else event_data
            event_type = event.get('type')

            # Bloquear captura temporal para evitar loops
            self.block_events = True

            if event_type == 'mouse_move':
                self.replay_mouse_move(event)
            elif event_type == 'mouse_click':
                self.replay_mouse_click(event)
            elif event_type == 'mouse_scroll':
                self.replay_mouse_scroll(event)
            elif event_type == 'key_press':
                self.replay_key_press(event)
            elif event_type == 'key_release':
                self.replay_key_release(event)
            elif event_type == 'control_change':
                self.controlling = event.get('controlling', False)
                if self.controlling:
                    self.log("Ahora TIENES el control del mouse/teclado", "success")
                else:
                    self.log("Control transferido al dispositivo REMOTO", "warning")

            # Desbloquear captura
            time.sleep(0.001)  # Pequeno delay para evitar race conditions
            self.block_events = False

        except Exception as e:
            self.block_events = False
            self.log(f"Error procesando evento remoto: {e}", "error")

    def replay_mouse_move(self, event):
        """Reproduce movimiento de mouse"""
        try:
            from tkinter import Tk
            root = Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()

            # Convertir de relativo a absoluto
            x = int(event['x'] * screen_width)
            y = int(event['y'] * screen_height)

            self.mouse_controller.position = (x, y)
        except Exception as e:
            self.log(f"Error moviendo mouse: {e}", "error")

    def replay_mouse_click(self, event):
        """Reproduce click de mouse"""
        try:
            button_name = event['button']
            pressed = event['pressed']

            button = getattr(Button, button_name, Button.left)

            if pressed:
                self.mouse_controller.press(button)
            else:
                self.mouse_controller.release(button)
        except Exception as e:
            self.log(f"Error reproduciendo click: {e}", "error")

    def replay_mouse_scroll(self, event):
        """Reproduce scroll de mouse"""
        try:
            dx = event['dx']
            dy = event['dy']
            self.mouse_controller.scroll(dx, dy)
        except Exception as e:
            self.log(f"Error reproduciendo scroll: {e}", "error")

    def replay_key_press(self, event):
        """Reproduce presion de tecla"""
        try:
            key = self.deserialize_key(event['key'])
            if key:
                self.keyboard_controller.press(key)
        except Exception as e:
            self.log(f"Error presionando tecla: {e}", "error")

    def replay_key_release(self, event):
        """Reproduce liberacion de tecla"""
        try:
            key = self.deserialize_key(event['key'])
            if key:
                self.keyboard_controller.release(key)
        except Exception as e:
            self.log(f"Error liberando tecla: {e}", "error")

    # === UTILIDADES ===

    def send_event(self, event):
        """Envia un evento al dispositivo remoto"""
        try:
            event_json = json.dumps(event)
            self.send_callback(event_json)
        except Exception as e:
            self.log(f"Error enviando evento: {e}", "error")

    def serialize_key(self, key):
        """Convierte una tecla a formato serializable"""
        try:
            if hasattr(key, 'char') and key.char is not None:
                return {'type': 'char', 'value': key.char}
            elif hasattr(key, 'name'):
                return {'type': 'special', 'value': key.name}
            else:
                return {'type': 'special', 'value': str(key)}
        except:
            return None

    def deserialize_key(self, key_data):
        """Convierte datos serializados de vuelta a una tecla"""
        try:
            if key_data['type'] == 'char':
                return keyboard.KeyCode.from_char(key_data['value'])
            elif key_data['type'] == 'special':
                # Intentar obtener la tecla especial por nombre
                try:
                    return getattr(Key, key_data['value'])
                except:
                    return None
        except:
            return None
