import hashlib
import json
import os
import urllib

RESET = "\033[0m"
RED = "\033[91m"

VIRUS_TOTAL = "https://www.virustotal.com/api/v3/files/"


def virustotal(file_path, virustotal_key=None):

    if not virustotal_key:

        virustotal_key = os.environ.get("VIRUSTOTAL_API_KEY")

        if not virustotal_key:

            return {
                "error":   "Configuration error.",
                "message": "No VirusTotal API key is configured. Set the VIRUSTOTAL_API_KEY environment variable or save a personal key in your account settings."
            }

    try:

        file_hash = hashlib.sha256()

        with open(file_path, "rb") as file:

            for block in iter(lambda: file.read(4096), b""):

                file_hash.update(block)

        file_hash = file_hash.hexdigest()
        headers = {"x-apikey": virustotal_key}
        api_request = urllib.request.Request(
            VIRUS_TOTAL + file_hash, headers=headers)

        try:

            with urllib.request.urlopen(api_request) as response:

                response_data = json.loads(response.read().decode())
                stats = response_data["data"]["attributes"]["last_analysis_stats"]
                return {
                    "file_hash":          file_hash,
                    "stats_malicious":    stats.get("malicious", 0),
                    "stats_suspicious":   stats.get("suspicious", 0),
                    "stats_undetected":   stats.get("undetected", 0),
                    "stats_harmless":     stats.get("harmless", 0),
                    "last_analysis_date": response_data["data"]["attributes"].get("last_analysis_date"),
                    "link":               f"https://www.virustotal.com/gui/file/{file_hash}",
                    "status":             "0" if stats.get("malicious", 0) == 0 and stats.get("suspicious", 0) == 0 else "1"
                }

        except urllib.error.HTTPError as exception:

            if exception.code == 404:

                return {
                    "file_hash": file_hash,
                    "message":   "This file has not previously been submitted to VirusTotal and no analysis results are available. You may submit it for analysis manually.",
                    "link":      "https://www.virustotal.com/gui/home/upload"
                }

            raise

    except Exception as exception:

        exception_string = str(exception).split(
            "]")[-1].strip() if "]" in str(exception) else str(exception)
        print(
            f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
        return {
            "error":   "SVirusTotal scan failed.",
            "details": str(exception)
        }
