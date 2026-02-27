import json
import os


def LoadSignatures():
    try:
        with open(os.path.join(os.path.dirname(__file__), "..", "data", "signatures.json"), "r", encoding="latin-1") as filerecord:
            signaturesource = json.load(filerecord)
    except Exception:
        return {}

    signatures = {}
    for signaturerecord in signaturesource:
        signaturehex = signaturerecord.get("HEX", "")
        signaturefiletype = signaturerecord.get("FILE_TYPE", "")
        signaturedescription = signaturerecord.get("DESCRIPTION", "")
        if signaturehex and signaturefiletype:
            signatures[bytes.fromhex(signaturehex)] = (signaturefiletype, signaturedescription)
    return signatures
