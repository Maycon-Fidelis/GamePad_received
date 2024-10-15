import asyncio
import websockets
import json
import uuid
import socket
import vgamepad as vg
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import qrcode
import threading
import webbrowser

connections = {}
users = {}
gamepads = {}
device_indices = {}
max_connections = 8
global ip_address
global port

ip_address = ''
port = ''

button_map = {
    'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    'LB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    'RB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    'SELECT': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    'HOME': vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    'UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    'DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    'LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    'RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    'RS': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    'LS': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB
}

async def handle_message(message, uuid):
    parsed_message = json.loads(message)
    user = users[uuid]
    gamepad = gamepads[uuid]

    if parsed_message.get('type') == 'control':
        button_event = parsed_message
        user['buttonHistory'].append(button_event)

        button = button_event.get('button')
        state = button_event.get('state')

        button_actions = {
            'press': lambda btn: gamepad.press_button(button=button_map[btn]),
            'release': lambda btn: gamepad.release_button(button=button_map[btn])
        }

        if button in button_map and state in button_actions:
            button_actions[state](button)

        elif button == 'LT':
            gamepad.left_trigger(value=255 if state == 'press' else 0)
        elif button == 'RT':
            gamepad.right_trigger(value=255 if state == 'press' else 0)


    elif parsed_message.get('type') == 'joystick':

        x_value = parsed_message.get('x', 0)
        y_value = parsed_message.get('y', 0)
        joystick_id = parsed_message.get('id')


        if joystick_id == 'joystick1':
            gamepad.left_joystick(x_value=x_value, y_value=y_value)
        elif joystick_id == 'joystick2':
            gamepad.right_joystick(x_value=x_value, y_value=y_value)

    gamepad.update()


async def handle_client(websocket, path):
    global device_indices
    if len(device_indices) >= max_connections:
        print("Connection limit reached. Rejecting new connection.")
        await websocket.close(code=4000)
        return


    try:
        name_message = await websocket.recv()
        name_data = json.loads(name_message)

        if 'username' in name_data:
            username = name_data['username']

            if username in [user['username'] for user in users.values()]:
                await websocket.send(json.dumps({"error": "Username alredy exist"}))
                await  websocket.close(code=4001)
                return

        else:
            username = f"User {uuid_str}"

        uuid_str = str(uuid.uuid4())
        print(f"New connection: UUID: {uuid_str}")

        connections[uuid_str] = websocket

        gamepad = vg.VX360Gamepad()
        gamepads[uuid_str] = gamepad
        
        users[uuid_str] = {
            'username': username,
            'state': {},
            'buttonHistory': []
        }

        device_indices[uuid_str] = len(device_indices) + 1

        add_device_to_gui(uuid_str, username)

        print(f"User {username} connected with UUID: {uuid_str}")

        async for message in websocket:
            await handle_message(message, uuid_str)

    finally:
        handle_close(uuid_str)
        print(f"Connection closed for UUID: {uuid_str}")
        remove_device_from_gui(uuid_str)


def handle_close(uuid):
    if uuid in connections:
        del connections[uuid]
    if uuid in users:
        del users[uuid]
    if uuid in gamepads:
        del gamepads[uuid]
    if uuid in device_indices:
        del device_indices[uuid]
    
    reindex_devices()

def reindex_devices():
    global device_indices
    sorted_uuids = sorted(device_indices.keys(), key=lambda x: device_indices[x])
    for index, uuid in enumerate(sorted_uuids):
        device_indices[uuid] = index + 1

def update_ip_port_label(ip, port):
    """Função para atualizar o texto do ip_port_label com o IP e porta obtidos."""
    ip_port_label.config(text=f"IP: {ip}\nPorta: {port}")


async def main_websocket():
    global ip_address
    port = 8083
    while True:
        try:
            server = await websockets.serve(handle_client, "0.0.0.0", port)
            ip_address = get_local_ip_address()
            print(f"WebSocket server is running at ws://{ip_address}:{port}")
            
            qr_img = generate_qr_code(ip_address, port)
            qr_label.config(image=qr_img)
            qr_label.image = qr_img
            
            update_ip_port_label(ip_address, port)
            break
        except OSError:
            port += 1

    await server.wait_closed()


def get_local_ip_address():
    interfaces = socket.getaddrinfo(socket.gethostname(), None)
    for interface in interfaces:
        if interface[0] == socket.AF_INET:
            return interface[4][0]
    return '127.0.0.1'

def start_websocket_server():
    asyncio.run(main_websocket())

translations = {
    'en': {
        'about_title': "About",
        'app_info': "Connection Manager\nDeveloped by [Your Name]\nVersion 1.0",
        'github': "GitHub: https://github.com/your-user",
        'project': "Project: https://your-project.com",
        'license': "Licensed under MIT",
        'used_libraries': "Libraries used:",
        'libraries': [
            "• asyncio (asynchronous IO management)",
            "• websockets (WebSocket server)",
            "• json (JSON data serialization)",
            "• vgamepad (virtual gamepad control)",
            "• tkinter (GUI interface)",
            "• ttkbootstrap (styles for tkinter)",
            "• PIL (image manipulation)",
            "• qrcode (QR code generation)"
        ],
        'language_button': "Change Language",
        'en': "English",
        'pt': "Portuguese",
        'text_help': "If you want, you can manually enter\n the port and IP values\n by clicking the button below",
        'toggle_button_show': "Show IP and Port",
        'toggle_button_hide': "Hide IP and Port",
        'device_count': "0/8 devices connected",
        'active_connections': "Active Connections",
        'new_feature_1': "Feature Description 1",
        'new_feature_2': "Feature Description 2",
    },
    'pt': {
        'about_title': "Sobre",
        'app_info': "Gerenciador de Conexões\nDesenvolvido por [Seu Nome]\nVersão 1.0",
        'github': "GitHub: https://github.com/seu-usuario",
        'project': "Projeto: https://seu-projeto.com",
        'license': "Licenciado sob MIT",
        'used_libraries': "Bibliotecas usadas:",
        'libraries': [
            "• asyncio (gerenciamento de IO assíncrono)",
            "• websockets (servidor WebSocket)",
            "• json (serialização de dados JSON)",
            "• vgamepad (controle virtual de gamepads)",
            "• tkinter (interface gráfica)",
            "• ttkbootstrap (estilos para tkinter)",
            "• PIL (manipulação de imagens)",
            "• qrcode (geração de QR codes)"
        ],
        'language_button': "Trocar Idioma",
        'en': "Inglês",
        'pt': "Português",
        'text_help': "Caso queira você pode digitar\nmanualmente os valores da porta\ne o ip clicando no botão abaixo",
        'toggle_button_show': "Mostrar IP e Porta",
        'toggle_button_hide': "Ocultar IP e Porta",
        'device_count': "0/8 dispositivos conectados",
        'active_connections': "Conexões Ativas",
        'new_feature_1': "Descrição da Funcionalidade 1",
        'new_feature_2': "Descrição da Funcionalidade 2",
    }
}

current_language = 'pt'

def generate_qr_code(ip, port):
    url = f"ws://{ip}:{port}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img = img.resize((250, 250))
    return ImageTk.PhotoImage(img)

def change_language():
    global current_language
    current_language = 'pt' if current_language == 'en' else 'en'
    update_ui_texts()

def update_ui_texts():
    about_button.config(text=translations[current_language]['about_title'])
    language_button.config(text=translations[current_language]['language_button'])
    toggle_button.config(text=translations[current_language]['toggle_button_show'] if not ip_port_label.winfo_ismapped() else translations[current_language]['toggle_button_hide'])

    device_count_label.config(text=translations[current_language]['device_count'])
    connection_label.config(text=translations[current_language]['active_connections'])
    text_help.config(text=translations[current_language]['text_help'])


def update_about_window_texts():
    about_window.title(translations[current_language]['about_title'])
    label.config(text=translations[current_language]['app_info'])
    github_label.config(text=translations[current_language]['github'])
    project_label.config(text=translations[current_language]['project'])
    license_info.config(text=translations[current_language]['license'])
    libraries_info.config(text=translations[current_language]['used_libraries'])

    for widget in about_window.winfo_children():
        if widget.winfo_name() == "library_label":
            widget.destroy()

    for lib in translations[current_language]['libraries']:
        lib_label = ttk.Label(about_window, text=lib, font=("Helvetica", 10), justify='center', name="library_label")
        lib_label.pack(anchor="center", padx=20)

def toggle_server_info():
    if not ip_port_label.winfo_ismapped():
        ip_port_label.grid(row=4, column=0, pady=5)
        toggle_button.config(text="Ocultar IP e Porta")
    else:
        ip_port_label.grid_remove()
        toggle_button.config(text="Mostrar IP e Porta")

async def disconnect_device(uuid):
    if uuid in connections:
        websocket = connections[uuid]
        await websocket.close()
    
    handle_close(uuid)
    remove_device_from_gui(uuid)

def update_device_count():
    device_count_label.config(text=f"{len(connections)}/{max_connections} dispositivos conectados")

def remove_device_from_gui(device_name):
    for widget in right_frame.winfo_children():
        if widget.winfo_name() == device_name:
            widget.destroy()
    
    if device_name in connections:
        threading.Thread(target=lambda: asyncio.run(disconnect_device(device_name))).start()
    
    update_device_count()

def add_device_to_gui(device_name, user_name):
    device_frame = ttk.Frame(right_frame, name=device_name)
    device_frame.grid(sticky="w", padx=10, pady=5)

    device_label = ttk.Label(device_frame, text=user_name, bootstyle="success", font=("Helvetica", 14), width=20)
    device_label.grid(row=0, column=0, padx=10, pady=5)

    remove_button = ttk.Button(device_frame, text="Remover", command=lambda: remove_device_from_gui(device_name), width=15)
    remove_button.grid(row=0, column=1, padx=(70,0), pady=5)

    style = ttk.Style()
    style.configure("my.TButton", font=("Helvetica", 12))
    remove_button.configure(style="my.TButton")

    update_device_count()

def show_about_info():
    global about_window, label, github_label, project_label, license_info, libraries_info
    about_window = tk.Toplevel(root)
    about_window.title(translations[current_language]['about_title'])
    about_window.geometry("400x500")
    
    label = ttk.Label(about_window, text=translations[current_language]['app_info'], font=("Helvetica", 12), justify="center")
    label.pack(pady=10)

    github_label = ttk.Label(about_window, text=translations[current_language]['github'], font=("Helvetica", 10), foreground="blue", cursor="hand2")
    github_label.pack(pady=5)
    github_label.bind("<Button-1>", lambda e: open_url("https://github.com/seu-usuario"))

    project_label = ttk.Label(about_window, text=translations[current_language]['project'], font=("Helvetica", 10), foreground="blue", cursor="hand2")
    project_label.pack(pady=5)
    project_label.bind("<Button-1>", lambda e: open_url("https://seu-projeto.com"))

    license_info = ttk.Label(about_window, text=translations[current_language]['license'], font=("Helvetica", 10))
    license_info.pack(pady=5)

    libraries_info = ttk.Label(about_window, text=translations[current_language]['used_libraries'], font=("Helvetica", 10))
    libraries_info.pack(pady=5)

    libs = [
        "• asyncio (gerenciamento de IO assíncrono)",
        "• websockets (servidor WebSocket)",
        "• json (serialização de dados JSON)",
        "• vgamepad (controle virtual de gamepads)",
        "• tkinter (interface gráfica)",
        "• ttkbootstrap (estilos para tkinter)",
        "• PIL (manipulação de imagens)",
        "• qrcode (geração de QR codes)"
    ]

    for lib in libs:
        lib_label = ttk.Label(about_window, text=lib, font=("Helvetica", 10), justify='center')
        lib_label.pack(anchor="center", padx=20)

def open_url(url):
    webbrowser.open_new(url)

root = ttk.Window(themename="darkly")
root.title("Gerenciador de Conexões")
root.geometry("900x550")

left_frame = ttk.Frame(root, padding=10)
left_frame.grid(row=0, column=0, sticky="ns")

right_frame = ttk.Frame(root, padding=10)
right_frame.grid(row=0, column=1, sticky="ns")

about_button = ttk.Button(left_frame, text=translations[current_language]['about_title'], command=show_about_info)
about_button.grid(row=0, column=0, pady=10)

ip_address = "127.0.0.1"
port = 8080
qr_img = generate_qr_code(ip_address, port)
qr_label = ttk.Label(left_frame, image=qr_img)
qr_label.grid(row=1, column=0, pady=10)

text_help = ttk.Label(left_frame, text=translations[current_language]['text_help'], bootstyle="info", font=(10), justify="center")
text_help.grid(row=2, column=0, pady=5)

language_button = ttk.Button(left_frame, text=translations[current_language]['language_button'], command=change_language)
language_button.grid(row=5, column=0, pady=10)

toggle_button = ttk.Button(left_frame, text=translations[current_language]['toggle_button_show'], command=toggle_server_info)
toggle_button.grid(row=3, column=0, pady=10)

ip_port_label = ttk.Label(left_frame, text=f"IP: {ip_address}\nPorta: {port}", bootstyle="info", font=(20))

device_count_label = ttk.Label(right_frame, text=translations[current_language]['device_count'], font=("Helvetica", 16))
device_count_label.grid(row=2, column=0, pady=10, padx=100)

connection_label = ttk.Label(right_frame, text=translations[current_language]['active_connections'], font=("Helvetica", 16))
connection_label.grid(row=1, column=0)

threading.Thread(target=start_websocket_server, daemon=True).start()

root.mainloop()