RESET = "\033[0m"
RED   = "\033[91m"

def read(file_path, number_of_bytes=None):

    try:

        with open(file_path, "rb") as file:

            return file.read(number_of_bytes) if number_of_bytes else file.read()

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
        return b""

def decode(number_of_bytes):

    if isinstance(number_of_bytes, (bytes, bytearray)):

        try:

            return number_of_bytes.rstrip(b"\x00").decode("utf-8", errors="replace").strip()

        except Exception as exception:

            exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
            print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
            return ""

    return str(number_of_bytes).strip()