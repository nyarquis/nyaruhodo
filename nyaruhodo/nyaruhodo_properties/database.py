import os
import sqlite3
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))

import common

RESET = "\033[0m"
RED   = "\033[91m"

def read(file_path, file_type):

    properties = {}

    try:

        file_bytes = common.read(file_path, 100)

        if file_bytes[:16] != b"SQLite format 3\x00":

            return properties

        pagesize = struct.unpack_from(">H", file_bytes, 16)[0]

        if pagesize == 1:

            pagesize = 65536

        text_encoding_code = struct.unpack_from(">I", file_bytes, 56)[0]
        user_version       = struct.unpack_from(">I", file_bytes, 60)[0]
        application_id     = struct.unpack_from(">I", file_bytes, 68)[0]
        schema_version     = struct.unpack_from(">I", file_bytes, 40)[0]
        properties["PageSize"]      = f"{pagesize} bytes"
        properties["TextEncoding"]  = {1: "UTF-8", 2: "UTF-16 LE", 3: "UTF-16 BE"}.get(text_encoding_code, str(text_encoding_code))
        properties["SchemaVersion"] = schema_version

        if user_version:

            properties["UserVersion"] = user_version

        if application_id:

            properties["ApplicationID"] = f"0x{application_id:08X}"

        try:

            connection = sqlite3.connect(f"file:{file_path}?mode=ro", uri=True)
            cursor     = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            properties["TableCount"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            properties["IndexCount"] = cursor.fetchone()[0]
            connection.close()

        except Exception as exception:

            exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
            print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")

    return properties