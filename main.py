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
    parsed_message = json.loads(message)
    user = users[uuid]
    gamepad = gamepads[uuid]

    if parsed_message['type'] == 'control':
        button_event = parsed_message['message']
        print(f"Button event: {json.dumps(button_event)}")
        user['buttonHistory'].append(button_event)

        button = button_event.get('button')
        state = button_event.get('state')

        if button in button_map:
            if state == 'press':
                gamepad.press_button(button=button_map[button])
            elif state == 'release':
                gamepad.release_button(button=button_map[button])
        elif button == 'LT':
            if state == 'press':
                gamepad.left_trigger(value=255)  # Pressed fully
            elif state == 'release':
                gamepad.left_trigger(value=0)    # Released
        elif button == 'RT':
            if state == 'press':
                gamepad.right_trigger(value=255)  # Pressed fully
            elif state == 'release':
                gamepad.right_trigger(value=0)    # Released

    elif parsed_message['type'] == 'joystick':
        log_message = parsed_message['message']
        joystick_data = log_message.get('joystick', {})
        if 'id' in joystick_data and joystick_data['id'] == 'joystick1':
            x_value = joystick_data.get('x', 0)
            y_value = joystick_data.get('y', 0)
            gamepad.left_joystick(x_value=x_value, y_value=y_value)
        elif 'id' in joystick_data and joystick_data['id'] == 'joystick2':
            x_value = joystick_data.get('x', 0)
            y_value = joystick_data.get('y', 0)
            gamepad.right_joystick(x_value=x_value, y_value=y_value)

    gamepad.update()

async def handle_client(websocket, path):
    global device_indices
    if len(device_indices) >= max_connections:
        print("Connection limit reached. Rejecting new connection.")
        await websocket.close(code=4000)
        return

    uuid_str = str(uuid.uuid4())
    print(f"New connection: UUID: {uuid_str}")

    connections[uuid_str] = websocket
    gamepad = vg.VX360Gamepad()
    gamepads[uuid_str] = gamepad

    users[uuid_str] = {
        'username': f"User {uuid_str}",
        'state': {},
        'buttonHistory': []
    }

    device_indices[uuid_str] = len(device_indices) + 1

    add_device_to_gui(uuid_str)

    try:
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
    port = 8082
    while True:
        try:
            server = await websockets.serve(handle_client, "0.0.0.0", port)
            ip_address = get_local_ip_address()
            print(f"WebSocket server is running at ws://{ip_address}:{port}")
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

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
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

def add_device_to_gui(device_name):
    device_frame = ttk.Frame(right_frame, name=device_name)
    device_frame.grid(sticky="w", padx=10, pady=5)

    device_label = ttk.Label(device_frame, text=device_name, bootstyle="success", font=("Helvetica", 14))
    device_label.grid(row=0, column=0, padx=10, pady=5)

    remove_button = ttk.Button(device_frame, text="Remover", command=lambda: remove_device_from_gui(device_name))
    remove_button.grid(row=0, column=1, padx=10, pady=5)

    style = ttk.Style()
    style.configure("my.TButton", font=("Helvetica", 12))
    remove_button.configure(style="my.TButton")

    update_device_count()

root = ttk.Window(themename="darkly")
root.title("Gerenciador de Conexões")
root.geometry("900x500")

left_frame = ttk.Frame(root, padding=10)
left_frame.grid(row=0, column=0, sticky="ns")

qr_code_data = "http://example.com"
qr_img = generate_qr_code(qr_code_data)
qr_label = ttk.Label(left_frame, image=qr_img)
qr_label.grid(row=0, column=0, pady=10)

text_help = ttk.Label(left_frame, text="Caso queira você pode digitar\nmanualmente os valores da porta\ne o ip Clicando no botão abaixo", bootstyle="info", font=(10), justify="center")
text_help.grid(row=1, column=0, pady=5)

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
