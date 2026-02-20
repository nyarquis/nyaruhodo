import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import nyaruhodo_signatures

RESET      = "\033[0m"
RED        = "\033[91m"
YELLOW     = "\033[93m"
SIGNATURES = None

def signatures():
    global SIGNATURES
    if SIGNATURES is None:
        SIGNATURES = nyaruhodo_signatures.load_signatures()
    return SIGNATURES

def get_header(file_path, byte_count=32):

    try:

        with open(file_path, "rb") as file:

            return file.read(byte_count)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
        return None

def compound_file(file_path, header):

    if header[:4] == b"RIFF":

        if header[8:12] == b"WEBP":

            return "WEBP", "WebP Image"

        if header[8:12] == b"AVI ":

            return "AVI", "AVI Video"

        if header[8:12] == b"WAVE":

            return "WAV", "WAV Audio"

    if header[:4] == b"PK\x03\x04":

        try:

            with open(file_path, "rb") as file:

                file.seek(0)
                file_start = file.read(2048)

                if b"word/" in file_start:

                    return "DOCX", "Microsoft Word Document"

                elif b"xl/" in file_start:

                    return "XLSX", "Microsoft Excel Spreadsheet"

                elif b"ppt/" in file_start:

                    return "PPTX", "Microsoft PowerPoint Presentation"

                else:

                    return "ZIP", "ZIP Archive"

        except Exception as exception:

            exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
            print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
            return "ZIP", "ZIP Archive"

    return None, None

def find_file_type(file_path):

    header     = get_header(file_path)

    if not header:

        return None, "Sorry! Unable to read file."

    for signature, (file_type, description) in signatures().items():

        if header.startswith(signature):

            if signature in [b"RIFF", b"PK\x03\x04"]:

                file_type, description = compound_file(file_path, header)

                if file_type:

                    return file_type, description

            return file_type, description

    try:

        with open(file_path, "r", encoding="utf-8") as file:

            file.read(1024)

        return "TXT", "Text Document"

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {YELLOW}WARNING{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")

    return "UNKNOWN", "Unknown File"

def get_file_type(filename):

    _, extension = os.path.splitext(filename)
    return extension[1:].upper() if extension else "NONE"

def scan(file_path, filename):

    original_file_type     = get_file_type(filename)
    file_type, description = find_file_type(file_path)
    mismatch               = False
    message                = "Sorry! File type could not be determined."

    if file_type == "UNKNOWN":

        message = "Sorry! File type is not in our database."

    elif original_file_type == "NONE":

        message  = f"File has no extension; we detected: {file_type}."
        mismatch = True

    elif original_file_type == file_type:

        message = f"File type is {original_file_type}; we detected: {file_type}."

    else:

        variations = {
            "JPG":  "JPEG",
            "JPEG": "JPG",
            "HTM":  "HTML",
            "HTML": "HTM",
            "TIF":  "TIFF",
            "TIFF": "TIF"
        }

        if variations.get(original_file_type) == file_type:

            message = f"File type is a valid variation of what we detected: {file_type}."

        else:

            message  = f"File type is not {original_file_type}; we detected: {file_type}."
            mismatch = True

    return {
        "filename":           filename,
        "extension":          original_file_type,
        "filetype":           file_type,
        "description":        description,
        "mismatch":           mismatch,
        "message":            message
    }