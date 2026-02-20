import re
import common

def read(file_path, file_type):

    file_bytes = read(file_path)
    properties = {}

    try:
    
        filetext = file_bytes.decode('latin1', errors='replace')
    
    except Exception as exception:
    
        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")
        return properties

    version_match = re.search(r'%PDF-(\d+\.\d+)', filetext)
    
    if version_match:
    
        properties['PDFVersion'] = version_match.group(1)

    info_match = re.search(r'/Info\s*<<(.*?)>>', filetext, re.DOTALL)
    
    if info_match:
    
        info_block = info_match.group(1)
    
        for field_name in ['Title', 'Author', 'Subject', 'Keywords', 'Creator', 'Producer', 'CreationDate', 'ModDate']:
    
            field_match = re.search(rf'/{field_name}\s*\(([^)]*)\)', info_block)
    
            if field_match:
    
                value = field_match.group(1).strip()
    
                if value:
    
                    properties[field_name] = value

    page_count = len(re.findall(r'/Type\s*/Page[^s]', filetext))
    
    if page_count:
    
        properties['PageCount'] = page_count

    if '/Encrypt' in filetext:
    
        properties['Encrypted'] = 'Yes'

    return properties