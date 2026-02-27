import nyaruhodo_signatures
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
SIGNATURES = None


def Signatures():
    global SIGNATURES
    if SIGNATURES is None:
        SIGNATURES = nyaruhodo_signatures.LoadSignatures()
    return SIGNATURES


def GetHeader(filepath, bytecount=32):
    try:
        with open(filepath, "rb") as filerecord:
            return filerecord.read(bytecount)
    except Exception as exception:
        exceptionstring = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exceptionstring.upper()}")
        return None


def ComposeCompoundFile(filepath, headerbytes):
    if headerbytes[:4] == b"RIFF":
        if headerbytes[8:12] == b"WEBP":
            return "WEBP", "WebP Image"
        if headerbytes[8:12] == b"AVI ":
            return "AVI", "Audio Video Interleave Video"
        if headerbytes[8:12] == b"WAVE":
            return "WAV", "Waveform Audio"

    if headerbytes[:4] == b"PK\x03\x04":
        try:
            with open(filepath, "rb") as filerecord:
                filerecord.seek(0)
                filebeginning = filerecord.read(2048)
                if b"word/" in filebeginning:
                    return "DOCX", "Microsoft Word Document"
                if b"xl/" in filebeginning:
                    return "XLSX", "Microsoft Excel Spreadsheet"
                if b"ppt/" in filebeginning:
                    return "PPTX", "Microsoft PowerPoint Presentation"
                return "ZIP", "Zip Archive"
        except Exception:
            return "ZIP", "Zip Archive"
    return None, None


def FindFileType(filepath):
    headerbytes = GetHeader(filepath)
    if not headerbytes:
        return None, "The file could not be read."

    for signaturebytes, (filetype, description) in Signatures().items():
        if headerbytes.startswith(signaturebytes):
            if signaturebytes in [b"RIFF", b"PK\x03\x04"]:
                compoundfiletype, compounddescription = ComposeCompoundFile(filepath, headerbytes)
                if compoundfiletype:
                    return compoundfiletype, compounddescription
            return filetype, description

    try:
        with open(filepath, "r", encoding="utf-8") as filerecord:
            filerecord.read(1024)
        return "TXT", "Text Document"
    except Exception as exception:
        exceptionstring = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {YELLOW}WARNING{RESET} [{os.path.basename(__file__)}]: {exceptionstring.upper()}")
    return "UNKNOWN", "Unknown File"


def GetFileType(filename):
    _, extension = os.path.splitext(filename)
    return extension[1:].upper() if extension else "NONE"


def AnalyseFile(filepath, filename):
    originalfiletype = GetFileType(filename)
    detectedfiletype, description = FindFileType(filepath)
    mismatch = False

    if detectedfiletype == "UNKNOWN":
        message = "The binary signature of this file does not match any entry in the signature database."
    elif originalfiletype == "NONE":
        message = f"This file has no extension. The detected file type is {detectedfiletype}."
        mismatch = True
    elif originalfiletype == detectedfiletype:
        message = f"The declared extension ({originalfiletype}) matches the detected file type ({detectedfiletype})."
    else:
        message = f"The declared extension is {originalfiletype}, but the binary signature identifies this file as {detectedfiletype}."
        mismatch = True

    return {
        "filename": filename,
        "extension": originalfiletype,
        "file_type": detectedfiletype,
        "description": description,
        "mismatch": mismatch,
        "message": message,
    }
