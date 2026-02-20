import json

def lookup_tables():

    with open("data/properties.json", "r", encoding="utf-8") as file:

        properties = json.load(file)

    lookup_tables = {}
    key_tables = [
        "EXIF TAGS",
        "GPS TAGS",
        "ORIENTATION",
        "RESOLUTION",
        "PE MACHINES",
        "PE SUBSYSTEMS",
        "PE CHARACTERISTICS",
        "ELF TYPES",
        "ELF MACHINES",
        "ELF OSABI",
    ]

    for table_key, table_value in properties.items():

        if table_key in key_tables:

            lookup_tables[table_name] = {int(key): value for key, value in table_value.items()}

        else:

            lookup_tables[table_name] = table_value

    return lookup_tables

LOOKUP_TABLES       = lookup_tables()
EXIF_TAGS           = LOOKUP_TABLES["EXIF TAGS"]
GPS_TAGS            = LOOKUP_TABLES["GPS TAGS"]
ORIENTATION         = LOOKUP_TABLES["ORIENTATION"]
RESOLUTION          = LOOKUP_TABLES["RESOLUTION"]
ID3v2_FRAMES_v24    = LOOKUP_TABLES["ID3v2 FRAMES v24"]
ID3v2_FRAMES_v22    = LOOKUP_TABLES["ID3v2 FRAMES v22"]
ID3v1_GENRES        = LOOKUP_TABLES["ID3v1 GENRES"]
PE_MACHINES         = LOOKUP_TABLES["PE MACHINES"]
PE_SUBSYSTEMS       = LOOKUP_TABLES["PE SUBSYSTEMS"]
PE_CHARACTERISTICS  = LOOKUP_TABLES["PE CHARACTERISTICS"]
ELF_TYPES           = LOOKUP_TABLES["ELF TYPES"]
ELF_MACHINES        = LOOKUP_TABLES["ELF MACHINES"]
ELF_OSABI           = LOOKUP_TABLES["ELF OSABI"]
XML_NAMESPACES      = LOOKUP_TABLES["XML NAMESPACES"]