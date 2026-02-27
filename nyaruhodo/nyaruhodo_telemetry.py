import datetime
import os

RESET   = "\033[0m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
HANDLES = {}

def Timestamp():

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def Handle(identifier):

    username = identifier.lower().strip() or "common"

    if username in HANDLES:

        return HANDLES[username]

    handle = open(os.path.join(os.path.dirname(__file__), "..", "data", "telemetry", f"{username}.log"), "a", encoding="utf-8")
    HANDLES[username] = handle

    return handle

def Write(identifier, level, message):

    handle = Handle(identifier)
    handle.write(f"[ {Timestamp()} ][ {level:<5} ] {message}\n")
    handle.flush()

def Debug(identifier, message):

    Write(identifier, "DEBUG", message.upper())
    print(f"==> DEBUG [ {Timestamp()} ]: {message.upper()}\n")

def Info(identifier, message):

    Write(identifier, "INFO", message.upper())
    print(f"==> {BLUE}INFO{RESET} [ {Timestamp()} ]: {message.upper()}\n")

def Warn(identifier, message):

    Write(identifier, "WARN", message.upper())
    print(f"==> {YELLOW}WARN{RESET} [ {Timestamp()} ]: {message.upper()}\n")

def Error(identifier, message):

    Write(identifier, "ERROR", message.upper())
    print(f"==> {RED}ERROR{RESET} [ {Timestamp()} ]: {message.upper()}\n")
