import hashlib
import json
import os
import urllib.error
import urllib.request

RESET               = "\033[0m"
RED                 = "\033[91m"
VIRUSTOTAL_ENDPOINT = "https://www.virustotal.com/api/v3/files/"

def VirusTotalLookup(filepath, virustotal_api_key=None):

    if not virustotal_api_key:

        virustotal_api_key = os.environ.get("VIRUSTOTAL_API_KEY")

        if not virustotal_api_key:

            return {
                "error": "Configuration error.",
                "message": "No VirusTotal API key is configured.",
            }

    try:

        hashdigest = hashlib.sha256()

        with open(filepath, "rb") as file:

            for datablock in iter(lambda: file.read(4096), b""):

                hashdigest.update(datablock)

        filehash = hashdigest.hexdigest()
        apirequest = urllib.request.Request(VIRUSTOTAL_ENDPOINT + filehash, headers={"x-apikey": virustotal_api_key})

        try:

            with urllib.request.urlopen(apirequest) as responseobject:

                responsedata = json.loads(responseobject.read().decode())
                statistics = responsedata["data"]["attributes"]["last_analysis_stats"]

                return {
                    "filehash":   filehash,
                    "virustotal_malicious":  statistics.get("malicious", 0),
                    "virustotal_suspicious": statistics.get("suspicious", 0),
                    "virustotal_undetected": statistics.get("undetected", 0),
                    "virustotal_harmless":   statistics.get("harmless", 0),
                    "link":       f"https://www.virustotal.com/gui/file/{filehash}",
                }

        except urllib.error.HTTPError as exception:

            if exception.code == 404:

                return {
                    "filehash": filehash,
                    "message":  "This file has not previously been submitted to VirusTotal.",
                    "link":     "https://www.virustotal.com/gui/home/upload",
                }

            raise

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

        return {"error": "VirusTotal request failed.", "message": str(exception)}