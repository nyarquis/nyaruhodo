import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import nyaruhodo_signatures as signatures

RESET      = "\033[0m"
RED        = "\033[91m"
YELLOW     = "\033[93m"
SIGNATURES = None
EXTENSIONS = {
    frozenset({"JPG", "JPEG"}),
    frozenset({"HTM", "HTML"}),
    frozenset({"TIF", "TIFF"}),
}

def Signatures():

    global SIGNATURES
    
    if SIGNATURES is None:
    
        SIGNATURES = signatures.LoadSignatures()
    
    return SIGNATURES

def GetHeader(filepath, bytecount=32):

    try:

        with open(filepath, "rb") as file:

            return file.read(bytecount)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

        return None

def ComposeCompoundFile(filepath, header):

    if header[:4] == b"RIFF":

        if header[8:12] == b"WEBP":

            return "WEBP", "WebP Image"

        if header[8:12] == b"AVI ":

            return "AVI", "Audio Video Interleave Video"

        if header[8:12] == b"WAVE":

            return "WAV", "Waveform Audio"

    if header[:4] == b"PK\x03\x04":

        try:

            with open(filepath, "rb") as file:

                file.seek(0)
                file_content = file.read(2048)

                if b"word/" in file_content:

                    return "DOCX", "Microsoft Word Document"

                if b"xl/" in file_content:

                    return "XLSX", "Microsoft Excel Spreadsheet"

                if b"ppt/" in file_content:

                    return "PPTX", "Microsoft PowerPoint Presentation"

                return "ZIP", "Zip Archive"

        except Exception as exception:

            exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
            print(f"==> {RED}WARN{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")
    
            return "ZIP", "Zip Archive"

    return None, None

def FindFileType(filepath):

    header = GetHeader(filepath)

    if not header:

        return None, "The file could not be read."

    for signature, (filetype, description) in Signatures().items():

        if header.startswith(signature):

            if signature in [b"RIFF", b"PK\x03\x04"]:

                compound_filetype, compound_description = ComposeCompoundFile(filepath, header)

                if compound_filetype:

                    return compound_filetype, compound_description

            return filetype, description

    try:

        with open(filepath, "r", encoding="utf-8") as file:

            file.read(1024)

        return "TXT", "Text Document"

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {YELLOW}WARNING{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

    return "UNKNOWN", "Unknown File"

def GetFileType(filename):

    _, extension = os.path.splitext(filename)

    return extension[1:].upper() if extension else "NONE"

def ExtensionsMatch(variant_one, variant_two):

    if variant_one == variant_two:

        return True

    return any(frozenset({variant_one, variant_two}) == item for item in EXTENSIONS)

def AnalyseFile(filepath, filename):

    original_filetype              = GetFileType(filename)
    detected_filetype, description = FindFileType(filepath)
    mismatch                       = False

    if detected_filetype == "UNKNOWN":

        message = "The binary signature of this file does not match any entry in the signature database."

    elif original_filetype == "NONE":

        message  = f"This file has no extension. The detected file type is {detected_filetype}."
        mismatch = True

    elif ExtensionsMatch(original_filetype, detected_filetype):
    
        message = f"The declared extension ({original_filetype}) matches the detected file type ({detected_filetype})."

    else:

        message  = f"The declared extension is {original_filetype}, but the binary signature identifies this file as {detected_filetype}."
        mismatch = True

    return {
        "filename":          filename,
        "original_filetype": original_filetype,
        "detected_filetype": detected_filetype,
        "description":       description,
        "mismatch":          mismatch,
        "message":           message,
    }
