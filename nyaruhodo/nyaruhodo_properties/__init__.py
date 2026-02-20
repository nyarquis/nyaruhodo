import os

from . import archive
from . import audio
from . import database
from . import document
from . import executable
from . import image
from . import markup

RESET = "\033[0m"
RED   = "\033[91m"

READERS = {
    "APK":    archive.read,
    "DLL":    executable.read,
    "DOCX":   archive.read,
    "ELF":    executable.read,
    "EXE":    executable.read,
    "HTM":    markup.read,
    "HTML":   markup.read,
    "JPEG":   image.read,
    "JPG":    image.read,
    "MP3":    audio.read,
    "PDF":    document.read,
    "PNG":    image.read,
    "PPTX":   archive.read,
    "SQLITE": database.read,
    "SVG":    markup.read,
    "XLSX":   archive.read,
    "XML":    markup.read,
    "ZIP":    archive.read,
}

def read(file_path, file_type):

    file_type = (file_type or "").upper()
    reader    = READERS.get(file_type)

    if not reader:

        return {}

    try:

        properties = reader(file_path, file_type)
        return {key: str(value) for key, value in properties.items() if value not in (None, "", [], {})}

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
        return {}