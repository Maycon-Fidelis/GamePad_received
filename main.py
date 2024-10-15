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
    parsed_message = json.loads(message)  # Decodificar a mensagem JSON
    user = users[uuid]
    gamepad = gamepads[uuid]

    # Verificar o tipo de mensagem para distinguir entre controle de botões e joystick
    if parsed_message.get('type') == 'control':
        # Processar eventos de controle de botões
        button_event = parsed_message
        user['buttonHistory'].append(button_event)  # Armazenar histórico de botões

        button = button_event.get('button')
        state = button_event.get('state')

        # Mapeamento de ações de botões (press/release)
        button_actions = {
            'press': lambda btn: gamepad.press_button(button=button_map[btn]),
            'release': lambda btn: gamepad.release_button(button=button_map[btn])
        }

        # Verificar se o botão está no mapeamento e executar a ação correspondente
        if button in button_map and state in button_actions:
            button_actions[state](button)
        # Processar gatilhos analógicos (LT e RT)
        elif button == 'LT':
            gamepad.left_trigger(value=255 if state == 'press' else 0)
        elif button == 'RT':
            gamepad.right_trigger(value=255 if state == 'press' else 0)

    # Verificar se a mensagem é do tipo 'joystick'
    elif parsed_message.get('type') == 'joystick':
        # Processar eventos de controle de joystick
        x_value = parsed_message.get('x', 0)
        y_value = parsed_message.get('y', 0)
        joystick_id = parsed_message.get('id')

        # Verificar qual joystick está sendo controlado e aplicar os valores
        if joystick_id == 'joystick1':
            gamepad.left_joystick(x_value=x_value, y_value=y_value)
        elif joystick_id == 'joystick2':
            gamepad.right_joystick(x_value=x_value, y_value=y_value)

    # Atualizar o estado do gamepad após cada evento
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
            
            # Atualize o QR code com o IP e porta
            qr_img = generate_qr_code(ip_address, port)
            qr_label.config(image=qr_img)
            qr_label.image = qr_img  # Necessário para manter a referência
            
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

def generate_qr_code(ip, port):
    url = f"ws://{ip}:{port}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img = img.resize((250, 250))
    return ImageTk.PhotoImage(img)

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

    # Aqui usamos o nome do usuário em vez do UUID
    device_label = ttk.Label(device_frame, text=user_name, bootstyle="success", font=("Helvetica", 14), width=20)
    device_label.grid(row=0, column=0, padx=10, pady=5)

    remove_button = ttk.Button(device_frame, text="Remover", command=lambda: remove_device_from_gui(device_name), width=15)
    remove_button.grid(row=0, column=1, padx=(70,0), pady=5)

    style = ttk.Style()
    style.configure("my.TButton", font=("Helvetica", 12))
    remove_button.configure(style="my.TButton")

    update_device_count()


root = ttk.Window(themename="darkly")
root.title("Gerenciador de Conexões")
root.geometry("900x550")


left_frame = ttk.Frame(root, padding=10)
left_frame.grid(row=0, column=0, sticky="ns")

def show_about_info():
    # Criar uma nova janela de nível superior para mostrar as informações
    about_window = tk.Toplevel(root)
    about_window.title("Sobre")
    about_window.geometry("400x450")
    
    # Nome e versão do projeto
    label = ttk.Label(about_window, text="Gerenciador de Conexões\nDesenvolvido por [Seu Nome]\nVersão 1.0", font=("Helvetica", 12), justify="center")
    label.pack(pady=10)

    # Link para o perfil do GitHub
    github_label = ttk.Label(about_window, text="GitHub: https://github.com/seu-usuario", font=("Helvetica", 10), foreground="blue", cursor="hand2")
    github_label.pack(pady=5)
    github_label.bind("<Button-1>", lambda e: open_url("https://github.com/seu-usuario"))

    # Link para o site do projeto (se houver)
    project_label = ttk.Label(about_window, text="Projeto: https://seu-projeto.com", font=("Helvetica", 10), foreground="blue", cursor="hand2")
    project_label.pack(pady=5)
    project_label.bind("<Button-1>", lambda e: open_url("https://seu-projeto.com"))

    # Informações sobre a licença
    license_info = ttk.Label(about_window, text="Licenciado sob MIT", font=("Helvetica", 10))
    license_info.pack(pady=5)

    # Bibliotecas usadas no projeto
    libraries_info = ttk.Label(about_window, text="Bibliotecas usadas:", font=("Helvetica", 10))
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
    import webbrowser
    webbrowser.open_new(url)

# Botão "Sobre" que chama a janela de informações
about_button = ttk.Button(left_frame, text="Sobre", command=show_about_info)
about_button.grid(row=0, column=0, pady=10)

qr_code_data = "http://example.com"
qr_img = generate_qr_code(ip_address, port)
qr_label = ttk.Label(left_frame, image=qr_img)
qr_label.grid(row=1, column=0, pady=10)

text_help = ttk.Label(left_frame, text="Caso queira você pode digitar\nmanualmente os valores da porta\ne o ip Clicando no botão abaixo", bootstyle="info", font=(10), justify="center")
text_help.grid(row=2, column=0, pady=5)

toggle_button = ttk.Button(left_frame, text="Mostrar IP e Porta", command=toggle_server_info)
toggle_button.grid(row=3, column=0, pady=10)

ip_port_label = ttk.Label(left_frame, text=f"IP: {ip_address}\nPorta: {port}", bootstyle="info", font=(20))

right_frame = ttk.Frame(root, padding=10)
right_frame.grid(row=0, column=1, sticky="ns")

device_count_label = ttk.Label(right_frame, text="0/8 dispositivos conectados", font=("Helvetica", 16))
device_count_label.grid(row=2, column=0, pady=10, padx=100)

connection_label = ttk.Label(right_frame, text="Conexões Ativas", font=("Helvetica", 16))
connection_label.grid(row=1, column=0)

threading.Thread(target=start_websocket_server, daemon=True).start()

root.mainloop()