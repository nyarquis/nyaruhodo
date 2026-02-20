import html.parser
import re
import xml.etree.ElementTree


class HTMLPropertiesParser(html.parser.HTMLParser):
    
    def __init__(self):
    
        super().__init__()
        self.collected_properties = {}
        self.title                = None
        self.inside_title         = False

    def handle_starttag(self, element, attrs):

        attrs = dict(attrs)

        if element == 'meta':

            name    = attrs.get('name', attrs.get('property', '')).strip()
            content = attrs.get('content', '').strip()

            if name and content:

                self.collected_properties[name] = content

            charset = attrs.get('charset', '')

            if charset:

                self.collected_properties['charset'] = charset

        elif element == 'title':

            self.inside_title = True

    def handle_data(self, data):

        if self.inside_title and self.title is None:

            self.title = data.strip()

    def handle_endtag(self, element):

        if element == 'title':

            self.inside_title = False

def read_html(file_path):

    properties = {}

    try:

        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:

            page_content = file.read(32768)

        page_parser = HTMLPropertiesParser()
        page_parser.feed(page_content)

        if page_parser.title:

            properties['Title'] = page_parser.title

        for key, value in page_parser.collected_properties.items():

            if value:

                properties[key] = value

    except Exception as exception:

        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")

    return properties

def read_xml(file_path):

    properties = {}

    try:

        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:

            xml_header = file.read(512)

        declaration_match = re.search(r'<\?xml[^?]*\?>', xml_header)

        if declaration_match:

            xml_declaration = declaration_match.group(0)

            for declaration_attribute in ['version', 'encoding', 'standalone']:

                declaration_attribute_match = re.search(rf'{declaration_attribute}=["\']([^"\']+)["\']', xml_declaration)

                if declaration_attribute_match:

                    properties[declaration_attribute.capitalize()] = declaration_attribute_match.group(1)

        xml_tree                  = xml.etree.ElementTree.parse(file_path)
        xml_root                  = xml_tree.getroot()
        properties['RootElement'] = xml_root.tag.split('}')[-1]
        properties['ChildCount']  = len(list(xml_root))

    except Exception as exception:

        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")

    return properties

def read(file_path, file_type):

    if file_type in ('HTML', 'HTM'):

        return read_html(file_path)

    if file_type in ('XML', 'SVG'):

        return read_xml(file_path)

    return {}