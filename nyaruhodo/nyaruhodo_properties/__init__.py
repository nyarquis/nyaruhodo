from .  import archive
from .  import audio
from .  import database
from .  import document
from .  import executable
from .  import image
from .  import markup

READERS = {
    "APK":      archive.extract,
    "DLL":      executable.extract,
    "DOCX":     archive.extract,
    "ELF":      executable.extract,
    "EXE":      executable.extract,
    "HTM":      markup.extract,
    "HTML":     markup.extract,
    "JPEG":     image.extract,
    "JPG":      image.extract,
    "MP3":      audio.extract,
    "PDF":      document.extract,
    "PNG":      image.extract,
    "PPTX":     archive.extract,
    "SQLITE":   database.extract,
    "SVG":      markup.extract,
    "XLSX":     archive.extract,
    "XML":      markup.extract,
    "ZIP":      archive.extract,
}

def read(file_path, file_type):

    file_type = (file_type or "").upper()
    reader   = READERS.get(file_type)

    if not reader:

        return {}

    try:

        properties = reader(file_path, file_type)
        return {key: str(value) for key, value in properties.items() if value not in (None, "", [], {})}

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")
        return {}
