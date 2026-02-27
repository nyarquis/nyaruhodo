import os

RESET = "\033[0m"
RED   = "\033[91m"

def Read(filepath, number_ofbytes=None):

    try:

        with open(filepath, "rb") as file:

            return file.read(number_ofbytes) if number_ofbytes else file.read()

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")
    
        return b""

def DecodeBytes(number_ofbytes):

    if isinstance(number_ofbytes, (bytes, bytearray)):

        try:

            return number_ofbytes.rstrip(b"\x00").decode("utf-8", errors="replace").strip()

        except Exception as exception:

            exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
            print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

            return ""

    return str(number_ofbytes).strip()

decode = DecodeBytes
read   = Read
