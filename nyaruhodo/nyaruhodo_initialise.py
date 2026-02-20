import os
import platform

RESET  = "\033[0m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"

def paint_screen():

    lines = [
        "\n",
        "  ▄▄     ▄▄▄                                              ▄▄",
        "  ██▄   ██▀                       █▄             █▄       ██",
        "  ███▄  ██             ▄          ██             ██       ██",
        "  ██ ▀█▄██ ██ ██ ▄▀▀█▄ ████▄██ ██ ████▄ ▄███▄ ▄████ ▄███▄ ██",
        "  ██   ▀██ ██▄██ ▄█▀██ ██   ██ ██ ██ ██ ██ ██ ██ ██ ██ ██   ",
        "▀██▀    ██▄▄▀██▀▄▀█▄██▄█▀  ▄▀██▀█▄██ ██▄▀███▀▄█▀███▄▀███▀ ██",
        "             ██                                             ",
        "           ▀▀▀                                              ",
    ]

    try:

        os.system("cls" if platform.system() == "Windows" else "clear")
        columns = os.get_terminal_size().columns

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
        columns = 80

    for line in lines:

        print(line.center(columns))

    try:

        print(f"\nSystem: {platform.system()} {platform.release()} ({platform.machine()})\nPython: {platform.python_version()}\n")

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")