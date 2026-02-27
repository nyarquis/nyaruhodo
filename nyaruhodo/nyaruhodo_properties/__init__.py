import os

from . import nyaruhodo_archive    as archive
from . import nyaruhodo_audio      as audio
from . import nyaruhodo_database   as database
from . import nyaruhodo_document   as document
from . import nyaruhodo_executable as executable
from . import nyaruhodo_image      as image
from . import nyaruhodo_markup     as markup

RESET = "\033[0m"
RED   = "\033[91m"

READERS = {
    "APK":    archive.Read,
    "DLL":    executable.Read,
    "DOCX":   archive.Read,
    "ELF":    executable.Read,
    "EXE":    executable.Read,
    "HTM":    markup.Read,
    "HTML":   markup.Read,
    "JPEG":   image.Read,
    "JPG":    image.Read,
    "MP3":    audio.Read,
    "PDF":    document.Read,
    "PNG":    image.Read,
    "PPTX":   archive.Read,
    "SQLITE": database.Read,
    "SVG":    markup.Read,
    "XLSX":   archive.Read,
    "XML":    markup.Read,
    "ZIP":    archive.Read,
}

def Read(filepath, filetype):

    filetype       = (filetype or "").upper()
    readerfunction = READERS.get(filetype)

    if not readerfunction:

        return {}

    try:

        properties = readerfunction(filepath, filetype)

        return {key: str(value) for key, value in properties.items() if value not in (None, "", [], {})}

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

        return {}

read = Read
