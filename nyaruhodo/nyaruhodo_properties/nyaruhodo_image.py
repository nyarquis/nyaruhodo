import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))

import nyaruhodo_common as common
import nyaruhodo_tables as tables

RESET            = "\033[0m"
RED              = "\033[91m"
FIELD_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}

def ReadRational(tiffbytes, offset, endian):

    numerator, denominator = struct.unpack_from(endian + "II", tiffbytes, offset)
   
    return f"{numerator}/{denominator}" if denominator != 0 else str(numerator)


def ReadDirectoryFieldValue(tiffbytes, tag, field_type, count, value_or_offset, endian):

    field_size         = FIELD_TYPE_SIZES.get(field_type, 1)
    total_size         = field_size * count
    packed_valuebytes = struct.pack(endian + "I", value_or_offset)[:total_size] if total_size <= 4 else tiffbytes

    try:

        if field_type == 2:

            fieldbytes = tiffbytes[value_or_offset:value_or_offset + count] if total_size > 4 else struct.pack(endian + "I", value_or_offset)[:count]
        
            return common.decode(fieldbytes)

        elif field_type in (3, 4):

            unpack_format = (endian + "H") if field_type == 3 else (endian + "I")
            element_size  = 2 if field_type == 3 else 4

            if total_size <= 4:

                unpacked_values = [struct.unpack_from(unpack_format, packed_valuebytes, index * element_size)[0] for index in range(min(count, 4 // element_size))]

            else:

                unpacked_values = [struct.unpack_from(unpack_format, tiffbytes, value_or_offset + index * element_size)[0] for index in range(count)]

            return unpacked_values[0] if count == 1 else unpacked_values

        elif field_type == 5:

            if count == 1:

               return ReadRational(tiffbytes, value_or_offset, endian)

            rationals = []

            for item in range(count):

                rationals.append(ReadRational(tiffbytes, value_or_offset + item * 8, endian))

            return rationals

        elif field_type == 7:

            fieldbytes = tiffbytes[value_or_offset:value_or_offset + count] if total_size > 4 else struct.pack(endian + "I", value_or_offset)[:count]
         
            return common.decode(fieldbytes)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

    return None

def ReadImageFileDirectory(tiffbytes, offset, endian, tag_name_map):

    tag_values = {}

    try:

        entry_count = struct.unpack_from(endian + "H", tiffbytes, offset)[0]
        offset     += 2

        for _ in range(entry_count):

            tag, field_type, count, value_or_offset = struct.unpack_from(endian + "HHII", tiffbytes, offset)
            offset                            += 12
            tag_name                           = tag_name_map.get(tag)

            if tag_name:

                value = ReadDirectoryFieldValue(tiffbytes, tag, field_type, count, value_or_offset, endian)

                if value is not None:

                    tag_values[tag_name] = value

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")

    return tag_values

def ConvertGpsDegreesMinutesSecondsToDecimal(coordinate_parts, hemisphere_ref):

    try:

        coordinate_list = coordinate_parts if isinstance(coordinate_parts, list) else [coordinate_parts]

        def parse_rational(rational_string):

            numerator, denominator = str(rational_string).split("/")

            return float(numerator) / float(denominator)

        degrees         = parse_rational(coordinate_list[0]) if len(coordinate_list) > 0 else 0
        minutes         = parse_rational(coordinate_list[1]) if len(coordinate_list) > 1 else 0
        seconds         = parse_rational(coordinate_list[2]) if len(coordinate_list) > 2 else 0
        decimal_degrees = degrees + minutes / 60 + seconds / 3600

        if hemisphere_ref in ("S", "W"):

            decimal_degrees = -decimal_degrees

        return round(decimal_degrees, 6)

    except Exception as exception:

        exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")
    
        return None

def ReadJPEG(filepath):

    filebytes = common.read(filepath)
    properties = {}

    if filebytes[:2] != b"\xff\xd8":

        return properties

    offset = 2

    while offset < len(filebytes) - 1:

        if filebytes[offset] != 0xFF:

            break

        marker = filebytes[offset + 1]

        if marker in (0xD8, 0xD9):

            offset += 2
     
            continue

        if offset + 4 > len(filebytes):

            break

        segment_length = struct.unpack_from(">H", filebytes, offset + 2)[0]
        segment_data   = filebytes[offset + 4: offset + 2 + segment_length]

        if marker == 0xE0 and segment_data[:4] == b"JFIF":

            if len(segment_data) >= 9:

                density_unit_byte         = segment_data[7]
                properties["Format"]      = "JFIF"
                properties["JFIFVersion"] = f"{segment_data[5]}.{segment_data[6]:02d}"
                properties["XDensity"]    = struct.unpack_from(">H", segment_data, 8)[0]
                properties["YDensity"]    = struct.unpack_from(">H", segment_data, 10)[0]

                if density_unit_byte == 1:

                    properties["DensityUnit"] = "DPI"

                elif density_unit_byte == 2:

                    properties["DensityUnit"] = "DPCM"

        elif marker == 0xE1 and segment_data[:4] == b"Exif":

            tiffbytes = segment_data[6:]

            if tiffbytes[:2] == b"II":

                endian = "<"

            elif tiffbytes[:2] == b"MM":

                endian = ">"

            else:

                offset += 2 + segment_length
          
                continue

            main_directory_offset = struct.unpack_from(endian + "I", tiffbytes, 4)[0]
            main_directory        = ReadImageFileDirectory(tiffbytes, main_directory_offset, endian, tables.EXIF_TAGS)

            for field_name, value in main_directory.items():

                if field_name == "Orientation":

                    properties[field_name] = tables.ORIENTATION.get(value, str(value))

                elif field_name == "ResolutionUnit":

                    properties[field_name] = tables.RESOLUTION.get(value, str(value))

                elif field_name not in ("ExifIFD", "GPSIFD"):

                    properties[field_name] = str(value)

            if "ExifIFD" in main_directory:

                exif_directory = ReadImageFileDirectory(tiffbytes, main_directory["ExifIFD"], endian, tables.EXIF_TAGS)

                for field_name, value in exif_directory.items():

                    if field_name not in properties and field_name != "GPSIFD":

                        properties[field_name] = str(value)

            if "GPSIFD" in main_directory:

                gps_directory = ReadImageFileDirectory(tiffbytes, main_directory["GPSIFD"], endian, tables.GPS_TAGS)
                latitude      = ConvertGpsDegreesMinutesSecondsToDecimal(gps_directory.get("GPSLatitude", ""), gps_directory.get("GPSLatitudeRef", ""))
                longitude     = ConvertGpsDegreesMinutesSecondsToDecimal(gps_directory.get("GPSLongitude", ""), gps_directory.get("GPSLongitudeRef", ""))

                if latitude is not None:

                    properties["GPSLatitude"] = f"{latitude} ({gps_directory.get("GPSLatitudeRef", "")})"

                if longitude is not None:

                    properties["GPSLongitude"] = f"{longitude} ({gps_directory.get("GPSLongitudeRef", "")})"

                if "GPSAltitude" in gps_directory:

                    properties["GPSAltitude"] = f"{gps_directory["GPSAltitude"]} Meters {"(Below Sea Level)" if gps_directory.get("GPSAltitudeRef") == 1 else "(Above Sea Level)"}"

                if "GPSDateStamp" in gps_directory:

                    properties["GPSDate"] = gps_directory["GPSDateStamp"]

        offset += 2 + segment_length

    offset = 2

    while offset < len(filebytes) - 1:

        if filebytes[offset] != 0xFF:

            break

        marker = filebytes[offset + 1]

        if marker in range(0xC0, 0xC4):

            if offset + 9 < len(filebytes):

                precision                 = filebytes[offset + 4]
                height                    = struct.unpack_from(">H", filebytes, offset + 5)[0]
                width                     = struct.unpack_from(">H", filebytes, offset + 7)[0]
                components                = filebytes[offset + 9]
                properties["ImageWidth"]  = width
                properties["ImageHeight"] = height
                properties["ColorDepth"]  = f"{precision}-bit"
                properties["Components"]  = {1: "Grayscale", 3: "YCbCr (color)", 4: "CMYK"}.get(components, str(components))

            break

        if marker in (0xD8, 0xD9):

            offset += 2

            continue

        if offset + 4 > len(filebytes):

            break

        segment_length  = struct.unpack_from(">H", filebytes, offset + 2)[0]
        offset         += 2 + segment_length

    return properties


def ReadPNG(filepath):

    filebytes = common.read(filepath)
    properties = {}

    if filebytes[:8] != b"\x89PNG\r\n\x1a\n":

        return properties

    offset = 8

    while offset < len(filebytes) - 8:

        try:

            chunk_length = struct.unpack_from(">I", filebytes, offset)[0]
            chunktype   = filebytes[offset + 4: offset + 8].decode("ascii", errors="replace")
            chunk_data   = filebytes[offset + 8: offset + 8 + chunk_length]

            if chunktype == "IHDR" and chunk_length >= 13:

                bit_depth                 = chunk_data[8]
                colortype                = chunk_data[9]
                interlaced                = chunk_data[12]
                colortype_labels         = {0: "Grayscale", 2: "RGB", 3: "Indexed", 4: "Grayscale+Alpha", 6: "RGBA"}
                properties["ImageWidth"]  = struct.unpack_from(">I", chunk_data, 0)[0]
                properties["ImageHeight"] = struct.unpack_from(">I", chunk_data, 4)[0]
                properties["ColorType"]   = colortype_labels.get(colortype, str(colortype))
                properties["BitDepth"]    = f"{bit_depth}-bit"
                properties["Interlaced"]  = "Yes" if interlaced == 1 else "No"

            elif chunktype == "tEXt":

                first_null = chunk_data.find(b"\x00")

                if first_null != -1:

                    key   = common.decode(chunk_data[:first_null])
                    value = common.decode(chunk_data[first_null + 1:])

                    if key and value:

                        properties[key] = value

            elif chunktype == "iTXt":

                first_null = chunk_data.find(b"\x00")

                if first_null != -1:

                    key             = common.decode(chunk_data[:first_null])
                    remainingbytes = chunk_data[first_null + 1:]
                    second_null     = remainingbytes.find(b"\x00", 2)

                    if second_null != -1:

                        third_null = remainingbytes.find(b"\x00", second_null + 1)

                        if third_null != -1:

                            value = common.decode(remainingbytes[third_null + 1:])

                            if key and value:

                                properties[key] = value

            elif chunktype == "pHYs" and chunk_length >= 9:

                pixels_per_unit_x = struct.unpack_from(">I", chunk_data, 0)[0]
                pixels_per_unit_y = struct.unpack_from(">I", chunk_data, 4)[0]
                density_unit_byte = chunk_data[8]

                if density_unit_byte == 1:

                    properties["XResolution"] = f"{round(pixels_per_unit_x * 0.0254)} DPI"
                    properties["YResolution"] = f"{round(pixels_per_unit_y * 0.0254)} DPI"

                else:

                    properties["XResolution"] = f"{pixels_per_unit_x} px/unit"
                    properties["YResolution"] = f"{pixels_per_unit_y} px/unit"

            elif chunktype == "tIME" and chunk_length >= 7:

                year                       = struct.unpack_from(">H", chunk_data, 0)[0]
                month                      = chunk_data[2]
                day                        = chunk_data[3]
                hour                       = chunk_data[4]
                minute                     = chunk_data[5]
                second                     = chunk_data[6]
                properties["LastModified"] = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} UTC"

            elif chunktype == "gAMA" and chunk_length == 4:

                gamma               = struct.unpack_from(">I", chunk_data)[0] / 100000
                properties["Gamma"] = f"{gamma:.5f}"

            offset += 12 + chunk_length

        except Exception as exception:

            exception_string = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
            print(f"==> {RED}ERROR{RESET} [ {os.path.basename(__file__)} ]: {exception_string.upper()}")
     
            break

    return properties

def Read(filepath, filetype):

    if filetype in ("JPEG", "JPG"):

        return ReadJPEG(filepath)

    if filetype == "PNG":

        return ReadPNG(filepath)

    return {}


read = Read
