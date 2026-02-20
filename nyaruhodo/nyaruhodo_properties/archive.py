import os
import sys
import xml.etree.ElementTree
import zipfile

sys.path.insert(0, os.path.dirname(__file__))

import tables

RESET = "\033[0m"
RED   = "\033[91m"

NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"

CORE_FIELDS = {
    "dc:title":          ("Title",          "dc"),
    "dc:creator":        ("Author",         "dc"),
    "dc:description":    ("Description",    "dc"),
    "dc:subject":        ("Subject",        "dc"),
    "dc:language":       ("Language",       "dc"),
    "cp:lastModifiedBy": ("LastModifiedBy", "cp"),
    "cp:revision":       ("Revision",       "cp"),
    "cp:keywords":       ("Keywords",       "cp"),
    "dcterms:created":   ("Created",        "dcterms"),
    "dcterms:modified":  ("Modified",       "dcterms"),
}

APP_FIELDS = [
    ("Application", "Application"), ("AppVersion", "AppVersion"),
    ("Pages", "PageCount"),         ("Words", "WordCount"),
    ("Characters", "CharacterCount"), ("Slides", "SlideCount"),
    ("Company", "Company"),
]

def microsoft_office(archive, entry_names, properties):

    if "docProps/core.xml" in entry_names:

        with archive.open("docProps/core.xml") as file:

            xml_root = xml.etree.ElementTree.parse(file).getroot()

            for xml_tag, (field_label, _namespace_prefix) in CORE_FIELDS.items():

                element = xml_root.find(xml_tag, tables.XML_NAMESPACES)

                if element is not None and element.text:

                    properties[field_label] = element.text.strip()

    if "docProps/app.xml" in entry_names:

        with archive.open("docProps/app.xml") as file:

            xml_root = xml.etree.ElementTree.parse(file).getroot()

            for xml_tag, field_label in APP_FIELDS:

                element = xml_root.find(f"{{{NAMESPACE}}}{xml_tag}")

                if element is not None and element.text:

                    properties[field_label] = element.text.strip()

def read_archive(archive, entry_names, properties):

    entries         = archive.infolist()
    total_size      = sum(entry.file_size     for entry in entries)
    compressed_size = sum(entry.compress_size for entry in entries)
    properties["UncompressedSize"] = f"{total_size:,} bytes"

    if total_size > 0:

        compression_percentage         = (1 - compressed_size / total_size) * 100
        properties["CompressionRatio"] = f"{compression_percentage:.1f}%"

    if entry_names:

        top_level     = [n for n in entry_names if n.count("/") == 0 or (n.count("/") == 1 and n.endswith("/"))]
        display_names = top_level if top_level else entry_names
        first_entries = display_names[:8]
        overflow_suffix               = f" ... (+{len(display_names) - 8} more)" if len(display_names) > 8 else ""
        properties["TopLevelEntries"] = ", ".join(first_entries) + overflow_suffix
    
def read(file_path, file_type):

    properties = {}

    try:

        with zipfile.ZipFile(file_path, "r") as archive:

            entry_names             = archive.namelist()
            properties["FileCount"] = len(entry_names)

            if "docProps/core.xml" in entry_names:

                microsoft_office(archive, entry_names, properties)

            else:

                read_archive(archive, entry_names, properties)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")

    return properties