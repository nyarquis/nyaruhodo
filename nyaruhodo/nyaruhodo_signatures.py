import json
import os

def LoadSignatures():

    try:

        with open(os.path.join(os.path.dirname(__file__), "..", "data", "signatures.json"), "r", encoding="latin-1") as file:

            file = json.load(file)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")
   
        return {}

    signatures = {}

    for item in file:

        signature             = item.get("signature", "")
        signature_filetype    = item.get("signature_filetype", "")
        signature_description = item.get("signature_description", "")

        if signature and signature_filetype:

            signatures[bytes.fromhex(signature)] = (signature_filetype, signature_description)

    return signatures
