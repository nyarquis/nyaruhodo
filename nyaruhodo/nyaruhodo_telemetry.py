import datetime
import os

RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
HANDLES = {}


def Timestamp():
    return datetime.datetime.now().strftime(" %Y-%m-%d %H:%M:%S ")


def Handle(identifier):
    username = identifier.lower().strip() or "anonymous"
    if username in HANDLES:
        return HANDLES[username]
    handlerecord = open(os.path.join(os.path.dirname(__file__), "..", "data", "telemetry", f"{username}.txt"), "a", encoding="utf-8")
    HANDLES[username] = handlerecord
    return handlerecord


def Write(identifier, levelname, message):
    handlerecord = Handle(identifier)
    handlerecord.write(f"[{Timestamp()}][{levelname:<8}] {message}\n")
    handlerecord.flush()


def Debug(identifier, message):
    Write(identifier, "DEBUG", message.upper())
    print(f"==> DEBUG [{Timestamp()}]: {message.upper()}\n")


def Info(identifier, message):
    Write(identifier, "INFO", message.upper())
    print(f"==> {BLUE}INFO{RESET} [{Timestamp()}]: {message.upper()}\n")


def Warning(identifier, message):
    Write(identifier, "WARNING", message.upper())
    print(f"==> {YELLOW}WARN{RESET} [{Timestamp()}]: {message.upper()}\n")


def Error(identifier, message):
    Write(identifier, "ERROR", message.upper())
    print(f"==> {RED}ERROR{RESET} [{Timestamp()}]: {message.upper()}\n")
