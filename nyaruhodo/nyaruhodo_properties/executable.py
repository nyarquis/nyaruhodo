import datetime
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))

import common
import tables

RESET = "\033[0m"
RED   = "\033[91m"

def pe_timestamp_to_string(timestamp):

    try:

        return datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")
        return f"Invalid Timestamp ({str(timestamp)})"

def read_pe(file_path):

    file_bytes = common.read(file_path, 4096)
    properties = {}

    if file_bytes[:2] != b"MZ":

        return properties

    try:

        pe_header_offset = struct.unpack_from("<I", file_bytes, 0x3C)[0]

        if file_bytes[pe_header_offset: pe_header_offset + 4] != b"PE\x00\x00":

            return properties

        machine_code          = struct.unpack_from("<H", file_bytes, pe_header_offset + 4)[0]
        section_count         = struct.unpack_from("<H", file_bytes, pe_header_offset + 6)[0]
        timestamp             = struct.unpack_from("<I", file_bytes, pe_header_offset + 8)[0]
        optional_header_size  = struct.unpack_from("<H", file_bytes, pe_header_offset + 20)[0]
        characteristics_flags = struct.unpack_from("<H", file_bytes, pe_header_offset + 22)[0]
        properties["Architecture"] = tables.PE_MACHINES.get(machine_code, f"0x{machine_code:04X}")
        properties["CompileTime"]  = pe_timestamp_to_string(timestamp)
        properties["SectionCount"] = section_count
        characteristic_labels = [label for flag, label in tables.PE_CHARACTERISTICS.items() if characteristics_flags & flag]

        if characteristic_labels:

            properties["Characteristics"] = ", ".join(characteristic_labels)

        if optional_header_size >= 68:

            optional_magic         = struct.unpack_from("<H", file_bytes, pe_header_offset + 24)[0]
            properties["PEFormat"] = "PE32+" if optional_magic == 0x20B else "PE32"
            subsystem_field_offset = pe_header_offset + 24 + (68 if optional_magic != 0x20B else 84)

            if subsystem_field_offset + 2 <= len(file_bytes):

                subsystem_code          = struct.unpack_from("<H", file_bytes, subsystem_field_offset)[0]
                properties["Subsystem"] = tables.PE_SUBSYSTEMS.get(subsystem_code, str(subsystem_code))

        section_table_offset = pe_header_offset + 24 + optional_header_size
        sections = []

        for section_index in range(section_count):

            section_entry_offset = section_table_offset + section_index * 40

            if section_entry_offset + 8 > len(file_bytes):

                break

            section_name = file_bytes[section_entry_offset: section_entry_offset + 8].rstrip(b"\x00").decode("ascii", errors="replace")
            sections.append(section_name)

        if sections:

            properties["Sections"] = ", ".join(sections)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")

    return properties

def read_elf(file_path):

    file_bytes = common.read(file_path, 64)
    properties = {}

    if file_bytes[:4] != b"\x7fELF":

        return properties

    try:

        word_size_class = file_bytes[4]
        byte_order_code = file_bytes[5]
        osabi_code      = file_bytes[6]
        endian          = "<" if byte_order_code == 1 else ">"
        properties["Class"]      = "64-bit" if word_size_class == 2 else "32-bit"
        properties["Endianness"] = "Little-endian" if byte_order_code == 1 else "Big-endian"
        properties["OS/ABI"]     = tables.ELF_OSABI.get(osabi_code, f"0x{osabi_code:02X}")
        elf_file_type = struct.unpack_from(endian + "H", file_bytes, 16)[0]
        machine_code  = struct.unpack_from(endian + "H", file_bytes, 18)[0]
        elf_version   = struct.unpack_from(endian + "I", file_bytes, 20)[0]
        properties["Type"]         = tables.ELF_TYPES.get(elf_file_type, f"0x{elf_file_type:04X}")
        properties["Architecture"] = tables.ELF_MACHINES.get(machine_code, f"0x{machine_code:04X}")
        properties["ELFVersion"]   = str(elf_version)

        if word_size_class == 2:

            entry_point              = struct.unpack_from(endian + "Q", file_bytes, 24)[0]
            properties["EntryPoint"] = f"0x{entry_point:016X}"

        else:

            entry_point              = struct.unpack_from(endian + "I", file_bytes, 24)[0]
            properties["EntryPoint"] = f"0x{entry_point:08X}"

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [{os.path.basename(__file__)}]: {exception_string.upper()}")

    return properties

def read(file_path, file_type):

    if file_type in ("EXE", "DLL"):

        return read_pe(file_path)

    if file_type == "ELF":

        return read_elf(file_path)

    return {}