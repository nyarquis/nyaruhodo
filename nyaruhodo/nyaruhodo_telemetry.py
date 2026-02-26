import datetime
import os

RESET  = "\033[0m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
HANDLES = {}

def timestamp():

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def handle(identifier):

    identifier = identifier.lower().strip() or "anonymous"

    if identifier in HANDLES:

        return HANDLES[identifier]

    handle           = open(os.path.join(os.path.join(os.path.dirname(__file__), "..", "data", "telemetry"), f"{identifier}.log"), "a", encoding="utf-8")
    HANDLES[identifier] = handle
    return handle

def write(identifier, level, message):

    handle(identifier).write(f"{timestamp()} [{level:<8}] {message}\n").upper()
    handle(identifier).flush()

def debug(identifier, message):

    write(identifier, "DEBUG", message)
    print(f"==> DEBUG [{timestamp()}]: {message}").upper()

def info(identifier, message):

    write(identifier, "INFO", message)
    print(f"==> {BLUE}INFO{RESET} [{timestamp()}]: {message}").upper()

def warning(identifier, message):

    write(identifier, "WARNING", message)
    print(f"==> {YELLOW}WARN{RESET} [{timestamp()}]: {message}").upper()

def error(identifier, message):

    write(identifier, "ERROR", message)
    print(f"==> {RED}ERROR{RESET} [{timestamp()}]: {message}").upper()