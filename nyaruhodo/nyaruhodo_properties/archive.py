import zipfile
import xml.etree.ElementTree
import tables

NAMESPACE = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'

CORE_FIELDS = {
    'dc:title':          ('Title',          'dc'),
    'dc:creator':        ('Author',         'dc'),
    'dc:description':    ('Description',    'dc'),
    'dc:subject':        ('Subject',        'dc'),
    'dc:language':       ('Language',       'dc'),
    'cp:lastModifiedBy': ('LastModifiedBy', 'cp'),
    'cp:revision':       ('Revision',       'cp'),
    'cp:keywords':       ('Keywords',       'cp'),
    'dcterms:created':   ('Created',        'dcterms'),
    'dcterms:modified':  ('Modified',       'dcterms'),
}

APP_FIELDS = [
    ('Application', 'Application'), ('AppVersion', 'AppVersion'),
    ('Pages', 'PageCount'),         ('Words', 'WordCount'),
    ('Characters', 'CharacterCount'), ('Slides', 'SlideCount'),
    ('Company', 'Company'),
]

def microsoft_office(archive, entry_names, properties):

    if 'docProps/core.xml' in entry_names:

        with archive.open('docProps/core.xml') as file:

            xml_root = xml.etree.ElementTree.parse(file).getroot()

            for xml_tag, (field_label, _namespace_prefix) in CORE_FIELDS.items():

                element = xml_root.find(xml_tag, XML_NAMESPACES)

                if element is not None and element.text:

                    properties[field_label] = element.text.strip()

    if 'docProps/app.xml' in entry_names:

        with archive.open('docProps/app.xml') as file:

            xml_root = xml.etree.ElementTree.parse(file).getroot()

            for xml_tag, field_label in APP_FIELDS:

                element = xml_root.find(f'{{{NAMESPACE}}}{xml_tag}')

                if element is not None and element.text:

                    properties[field_label] = element.text.strip()

def archive(archive, entry_names, properties):

    total_size      = sum(entry.file_size     for entry in archive.infolist())
    compressed_size = sum(entry.compress_size for entry in archive.infolist())
    properties['UncompressedSize'] = f'{total_size:,} bytes'

    if total_size > 0:

        compression_percentage         = (1 - compressed_size / total_size) * 100
        properties['CompressionRatio'] = f'{compression_percentage:.1f}%'

    if entry_names:

        first_entries                  = entry_names[:8]
        overflow_suffix                = f' ... (+{len(entry_names) - 8} more)' if len(entry_names) > 8 else ''
        properties['TopLevelEntries']  = ', '.join(first_entries) + overflow_suffix

def read(file_path, file_type):

    properties = {}

    try:

        with zipfile.ZipFile(file_path, 'r') as archive:

            entry_names                = archive.namelist()
            properties['FileCount']    = len(entry_names)
            has_office_properties      = file_type in ('DOCX', 'XLSX', 'PPTX') or 'docProps/core.xml' in entry_names

            if has_office_properties:

                microsoft_office(archive, entry_names, properties)

            else:

                archive(archive, entry_names, properties)

    except Exception as exception:

        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")

    return properties