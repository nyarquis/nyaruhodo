import os

from . import archive
from . import audio
from . import database
from . import document
from . import executable
from . import image
from . import markup

RESET = "\033[0m"
RED = "\033[91m"

READERS = {
    "APK": archive.Read,
    "DLL": executable.Read,
    "DOCX": archive.Read,
    "ELF": executable.Read,
    "EXE": executable.Read,
    "HTM": markup.Read,
    "HTML": markup.Read,
    "JPEG": image.Read,
    "JPG": image.Read,
    "MP3": audio.Read,
    "PDF": document.Read,
    "PNG": image.Read,
    "PPTX": archive.Read,
    "SQLITE": database.Read,
    "SVG": markup.Read,
    "XLSX": archive.Read,
    "XML": markup.Read,
    "ZIP": archive.Read,
}


def Read(filepath, filetype):
    filetype = (filetype or "").upper()
    readerfunction = READERS.get(filetype)
    if not readerfunction:
        return {}
    try:
        properties = readerfunction(filepath, filetype)
        return {key: str(value) for key, value in properties.items() if value not in (None, "", [], {})}
    except Exception as exception:
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {str(exception).upper()}")
        return {}


read = Read
