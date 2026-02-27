import hashlib
import json
import os
import urllib.error
import urllib.request

RESET = "\033[0m"
RED = "\033[91m"

VIRUSTOTAL_ENDPOINT = "https://www.virustotal.com/api/v3/files/"


def VirusTotalLookup(filepath, virustotalkey=None):
    if not virustotalkey:
        virustotalkey = os.environ.get("VIRUSTOTAL_API_KEY")
        if not virustotalkey:
            return {
                "error": "Configuration error.",
                "message": "No VirusTotal API key is configured.",
            }

    try:
        hashdigest = hashlib.sha256()
        with open(filepath, "rb") as filerecord:
            for datablock in iter(lambda: filerecord.read(4096), b""):
                hashdigest.update(datablock)

        filehash = hashdigest.hexdigest()
        apirequest = urllib.request.Request(VIRUSTOTAL_ENDPOINT + filehash, headers={"x-apikey": virustotalkey})

        try:
            with urllib.request.urlopen(apirequest) as responseobject:
                responsedata = json.loads(responseobject.read().decode())
                statistics = responsedata["data"]["attributes"]["last_analysis_stats"]
                return {
                    "file_hash": filehash,
                    "stats_malicious": statistics.get("malicious", 0),
                    "stats_suspicious": statistics.get("suspicious", 0),
                    "stats_undetected": statistics.get("undetected", 0),
                    "stats_harmless": statistics.get("harmless", 0),
                    "link": f"https://www.virustotal.com/gui/file/{filehash}",
                }
        except urllib.error.HTTPError as exception:
            if exception.code == 404:
                return {
                    "file_hash": filehash,
                    "message": "This file has not previously been submitted to VirusTotal.",
                    "link": "https://www.virustotal.com/gui/home/upload",
                }
            raise
    except Exception as exception:
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {str(exception).upper()}")
        return {"error": "VirusTotal request failed.", "details": str(exception)}
