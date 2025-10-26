# Clipboard Sync

Sincronizador de portapapeles en tiempo real entre Windows y Linux (Kali).

## Descripción

Este programa permite compartir automáticamente el contenido del portapapeles entre dos dispositivos conectados a través de internet o red local. Cuando copias texto en un dispositivo, automáticamente aparece en el portapapeles del otro dispositivo.

## Características

- Sincronización automática en tiempo real
- **Comparte portapapeles Y mouse/teclado entre dispositivos**
- Funciona entre Windows y Linux (Kali)
- Arquitectura cliente-servidor simple
- Detección automática de cambios
- **Interfaz gráfica (GUI) fácil de usar**
- **Se oculta en la bandeja del sistema (system tray)**
- **Compilable a ejecutable .exe (no requiere Python)**
- **Versión de línea de comandos también disponible**
- **Hotkey para cambiar control entre dispositivos (Ctrl+Alt+Shift+S)**
- Sin necesidad de configuración compleja

## Requisitos

### Windows (Laptop)
- Python 3.6 o superior
- pip

### Linux (Kali)
- Python 3.6 o superior
- pip
- xclip o xsel (para acceso al portapapeles)

## Instalación

### En ambos dispositivos:

1. Clona o descarga este proyecto

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

### Instalación adicional en Kali Linux:

```bash
sudo apt update
sudo apt install xclip
```

## Compilar a Ejecutable (.exe)

Si quieres usar la aplicación sin instalar Python, puedes compilarla a un archivo .exe:

### En Windows:
1. Asegúrate de tener todas las dependencias instaladas: `pip install -r requirements.txt`
2. Doble clic en `Compilar_a_EXE.bat`
3. O ejecuta: `python build_exe.py`
4. El archivo `ClipboardSync.exe` se creará en la carpeta `dist/`
5. Puedes copiar este .exe a cualquier ubicación y ejecutarlo directamente

**Ventajas del .exe:**
- No necesitas Python instalado
- Más fácil de distribuir
- Se ejecuta directamente con doble clic
- Más profesional

---

## Uso

### OPCIÓN 1: Interfaz Gráfica (RECOMENDADO)

La forma más fácil de usar Clipboard Sync es con la interfaz gráfica.

**En Windows:**
- Doble clic en `Iniciar_Clipboard_Sync.bat`
- O ejecuta: `python clipboard_sync_gui.py`

**En Linux/Kali:**
```bash
# Dar permisos al script (solo la primera vez)
chmod +x start_clipboard_sync.sh

# Ejecutar
./start_clipboard_sync.sh
# O directamente:
python3 clipboard_sync_gui.py
```

#### Configurar como Servidor:
1. Ejecuta la aplicación GUI
2. Selecciona **"Servidor"** en el modo de operación
3. Haz clic en **"Obtener IP Local"** para ver tu IP
4. Ingresa un puerto (por ejemplo: 5555)
5. Haz clic en **"Iniciar"**
6. Comparte tu IP con el cliente

#### Configurar como Cliente:
1. Ejecuta la aplicación GUI
2. Selecciona **"Cliente"** en el modo de operación
3. Ingresa la IP del servidor en el campo "IP"
4. Ingresa el mismo puerto que el servidor
5. Haz clic en **"Iniciar"**

¡Listo! Ahora cualquier texto que copies en un dispositivo aparecerá automáticamente en el otro.

**Funcionalidad de Bandeja del Sistema (System Tray):**
- La aplicación se oculta en la bandeja del sistema al minimizarla o cerrarla
- Haz clic derecho en el ícono de la bandeja para ver las opciones:
  - **Mostrar**: Abre la ventana principal
  - **Ocultar**: Oculta la ventana
  - **Estado**: Muestra el estado actual en una notificación
  - **Salir**: Cierra completamente la aplicación
- Doble clic en el ícono para mostrar/ocultar la ventana
- La aplicación seguirá sincronizando incluso cuando esté oculta

**Compartir Mouse/Teclado (KVM):**
- Una vez que la sincronización esté activa, marca la casilla "Activar compartir mouse/teclado"
- El dispositivo que active primero tendrá el control inicial
- **Para cambiar el control**: Presiona `Ctrl+Alt+Shift+S` en cualquier dispositivo
- El control cambiará al otro dispositivo automáticamente
- Puedes ver quién tiene el control en el indicador de estado
- Útil para trabajar con dos PCs sin cambiar el mouse/teclado físicamente

**Nota importante:**
- No hay datos hardcodeados
- La configuración se guarda automáticamente cada vez que inicias
- La próxima vez que abras la aplicación, se cargarán tus últimas configuraciones

---

### OPCIÓN 2: Línea de Comandos

Si prefieres usar comandos de terminal:

#### Paso 1: Configurar el servidor

Decide qué dispositivo será el servidor (puede ser cualquiera de los dos).

**En el servidor** (ejemplo: Windows):

```bash
python clipboard_sync.py server
```

Esto mostrará algo como:
```
[*] Servidor escuchando en 0.0.0.0:5555
[*] IP local: 192.168.1.100
```

Anota la IP local que aparece, la necesitarás para el cliente.

#### Paso 2: Conectar el cliente

**En el otro dispositivo** (ejemplo: Kali Linux), conéctate usando la IP del servidor:

```bash
python clipboard_sync.py client --host 192.168.1.100
```

Reemplaza `192.168.1.100` con la IP que anotaste del servidor.

#### Ejemplos de uso

**Servidor en puerto personalizado:**
```bash
python clipboard_sync.py server --port 6000
```

**Cliente conectando a puerto personalizado:**
```bash
python clipboard_sync.py client --host 192.168.1.100 --port 6000
```

---

## Cómo funciona

1. Una vez conectados ambos dispositivos, copia cualquier texto en uno de ellos
2. El programa detectará el cambio automáticamente
3. El texto se sincronizará al otro dispositivo
4. Funciona en ambas direcciones simultáneamente

## Configuración de red

### Red Local (LAN)
Si ambos dispositivos están en la misma red WiFi/Ethernet:
- Usa la IP local mostrada por el servidor
- No necesitas configuración adicional

### A través de Internet
Si los dispositivos están en redes diferentes:

**Opción 1: Port Forwarding**
- Configura port forwarding en el router del servidor al puerto 5555
- El cliente debe conectarse a la IP pública del servidor

**Opción 2: VPN**
- Usa una VPN como Tailscale o ZeroTier
- Conecta ambos dispositivos a la misma VPN
- Usa las IPs de la VPN para conectar

## Solución de problemas

### Error: "No connection could be made"
- Verifica que el servidor esté corriendo
- Comprueba que la IP sea correcta
- Asegúrate de que el firewall no esté bloqueando el puerto

### En Linux: "Could not find a copy/paste mechanism"
```bash
sudo apt install xclip
```

### El portapapeles no se sincroniza
- Verifica que ambos programas estén corriendo
- Comprueba que la conexión esté establecida
- Intenta copiar texto nuevo (no el mismo que ya estaba)

### Firewall Windows
Si el cliente no puede conectarse, permite el programa en el firewall:
1. Panel de Control > Firewall de Windows
2. Permitir una aplicación a través del Firewall
3. Agregar Python

## Detener el programa

En cualquier momento presiona `Ctrl+C` para detener el programa.

## Notas de seguridad

- Este programa NO encripta los datos
- Solo úsalo en redes confiables o a través de VPN
- No compartas información sensible sin medidas de seguridad adicionales
- El programa solo funciona con texto, no con archivos o imágenes

## Comandos de ayuda

Para ver todas las opciones disponibles:
```bash
python clipboard_sync.py --help
```

## Arquitectura

```
┌─────────────┐                    ┌─────────────┐
│   Windows   │                    │    Kali     │
│   (Server)  │◄──────────────────►│  (Client)   │
│             │   Internet/LAN     │             │
│  Puerto:5555│                    │             │
└─────────────┘                    └─────────────┘
       ▲                                  ▲
       │                                  │
   Clipboard                          Clipboard
   Monitoring                         Monitoring
```

## Licencia

Este proyecto es de código abierto y está disponible para uso personal y educativo.
