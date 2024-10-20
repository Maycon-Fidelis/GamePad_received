import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["asyncio", "websockets", "json", "uuid", "socket", "vgamepad", "tkinter", "ttkbootstrap", "PIL", "qrcode", "threading", "webbrowser"],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="GamePad Receiver",
    version="1.0",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, icon="icon.png")]
)
