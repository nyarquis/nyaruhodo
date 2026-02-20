import json
import time

RESET   = "\033[0m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"

def load_signatures():

    SIGNATURES  = {}

    try:

        signatures_count    = 0

        with open("data/signatures.json", "r", encoding="utf-8") as file:

            signatures  = json.load(file)

        for signature in signatures:

            signature_hex           = signature.get("HEX", "")
            signature_file_type      = signature.get("file_type", "")
            signature_description   = signature.get("DESCRIPTION", "")

            if not signature_hex or not signature_file_type:

                continue

            try:

                print(f"Loading Signature for {signature_description}", end = " ")
                load_time                   = 3
                signature_bytes             = bytes.fromhex(signature_hex)
                SIGNATURES[signature_bytes] = (signature_file_type, signature_description)
                signatures_count           += 1
                
                while load_time:
                    
                    print(".", end = "", flush = True)
                    time.sleep(0.1)
                    load_time  -= 1

                print(f" {GREEN}DONE{RESET}")

            except Exception as exception:

                exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
                print(f"==> {YELLOW}WARNING{RESET}: {exception_string.upper()} ({signature_hex.upper()})")
                continue

        if signatures_count:

            print(f"\n==> {GREEN}SUCCESS{RESET}: LOADED {signatures_count} SIGNATURES")
        
        else:

            print(f"\n==> {RED}ERROR{RESET}: NO SIGNATURES LOADED")

    except Exception as exception:

        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")
        return {}
    
    return SIGNATURES