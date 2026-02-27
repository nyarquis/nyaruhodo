import datetime
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))

import nyaruhodo_common as common
import nyaruhodo_tables as tables

RESET = "\033[0m"
RED   = "\033[91m"

def ConvertPortableExecutableTimestampToString(Timestamp):

    try:

        return datetime.datetime.utcfromtimestamp(Timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")
      
        return f"Invalid Timestamp ({str(Timestamp)})"

def ReadPE(filepath):

    filebytes = common.read(filepath, 4096)
    properties = {}

    if filebytes[:2] != b"MZ":

        return properties

    try:

        pe_header_offset = struct.unpack_from("<I", filebytes, 0x3C)[0]

        if filebytes[pe_header_offset: pe_header_offset + 4] != b"PE\x00\x00":

            return properties

        machine_code               = struct.unpack_from("<H", filebytes, pe_header_offset + 4)[0]
        section_count              = struct.unpack_from("<H", filebytes, pe_header_offset + 6)[0]
        Timestamp                  = struct.unpack_from("<I", filebytes, pe_header_offset + 8)[0]
        optional_header_size       = struct.unpack_from("<H", filebytes, pe_header_offset + 20)[0]
        characteristics_flags      = struct.unpack_from("<H", filebytes, pe_header_offset + 22)[0]
        characteristic_labels      = [label for flag, label in tables.PE_CHARACTERISTICS.items() if characteristics_flags & flag]
        properties["Architecture"] = tables.PE_MACHINES.get(machine_code, f"0x{machine_code:04X}")
        properties["CompileTime"]  = ConvertPortableExecutableTimestampToString(Timestamp)
        properties["SectionCount"] = section_count

        if characteristic_labels:

            properties["Characteristics"] = ", ".join(characteristic_labels)

        if optional_header_size >= 68:

            optional_magic         = struct.unpack_from("<H", filebytes, pe_header_offset + 24)[0]
            properties["PEFormat"] = "PE32+" if optional_magic == 0x20B else "PE32"
            subsystem_field_offset = pe_header_offset + 24 + (68 if optional_magic != 0x20B else 84)

            if subsystem_field_offset + 2 <= len(filebytes):

                subsystem_code          = struct.unpack_from("<H", filebytes, subsystem_field_offset)[0]
                properties["Subsystem"] = tables.PE_SUBSYSTEMS.get(subsystem_code, str(subsystem_code))

        section_table_offset = pe_header_offset + 24 + optional_header_size
        sections = []

        for section_index in range(section_count):

            section_entry_offset = section_table_offset + section_index * 40

            if section_entry_offset + 8 > len(filebytes):

                break

            section_name = filebytes[section_entry_offset: section_entry_offset + 8].rstrip(b"\x00").decode("ascii", errors="replace")
            sections.append(section_name)

        if sections:

            properties["Sections"] = ", ".join(sections)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

    return properties

def ReadELF(filepath):

    filebytes = common.read(filepath, 64)
    properties = {}

    if filebytes[:4] != b"\x7fELF":

        return properties

    try:

        word_size_class            = filebytes[4]
        byte_order_code            = filebytes[5]
        osabi_code                 = filebytes[6]
        elf_filetype              = struct.unpack_from(endian + "H", filebytes, 16)[0]
        machine_code               = struct.unpack_from(endian + "H", filebytes, 18)[0]
        elf_version                = struct.unpack_from(endian + "I", filebytes, 20)[0]
        endian                     = "<" if byte_order_code == 1 else ">"
        properties["Class"]        = "64-bit" if word_size_class == 2 else "32-bit"
        properties["Endianness"]   = "Little-endian" if byte_order_code == 1 else "Big-endian"
        properties["OS/ABI"]       = tables.ELF_OSABI.get(osabi_code, f"0x{osabi_code:02X}")
        properties["Type"]         = tables.ELF_TYPES.get(elf_filetype, f"0x{elf_filetype:04X}")
        properties["Architecture"] = tables.ELF_MACHINES.get(machine_code, f"0x{machine_code:04X}")
        properties["ELFVersion"]   = str(elf_version)

        if word_size_class == 2:

            entry_point              = struct.unpack_from(endian + "Q", filebytes, 24)[0]
            properties["EntryPoint"] = f"0x{entry_point:016X}"

        else:

            entry_point              = struct.unpack_from(endian + "I", filebytes, 24)[0]
            properties["EntryPoint"] = f"0x{entry_point:08X}"

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

    return properties

def Read(filepath, filetype):

    if filetype in ("EXE", "DLL"):

        return ReadPE(filepath)

    if filetype == "ELF":

        return ReadELF(filepath)

    return {}

read = Read
