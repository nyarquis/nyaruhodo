import struct
import common
import tables

FIELD_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}

def read_rational(tiff_bytes, offset, endian):

    numerator, denominator = struct.unpack_from(endian + "II", tiff_bytes, offset)
    return f"{numerator}/{denominator}" if denominator != 0 else str(numerator)

def read_directory_field_value(tiff_bytes, tag, type_, count, value_or_offset, endian):

    field_size        = FIELD_TYPE_SIZES.get(type_, 1)
    total_size        = field_size * count
    packed_value_bytes = struct.pack(endian + "I", value_or_offset)[:total_size] if total_size <= 4 else tiff_bytes

    try:

        if type_ == 2:

            field_bytes = tiff_bytes[value_or_offset:value_or_offset + count] if total_size > 4 else struct.pack(endian + "I", value_or_offset)[:count]
            return decode(field_bytes)

        elif type_ in (3, 4):

            unpack_format   = (endian + "H") if type_ == 3 else (endian + "I")
            element_size    = 2 if type_ == 3 else 4

            if total_size <= 4:

                unpacked_values = [struct.unpack_from(unpack_format, packed_value_bytes, index * element_size)[0] for index in range(min(count, 4 // element_size))]

            else:

                unpacked_values = [struct.unpack_from(unpack_format, tiff_bytes, value_or_offset + index * element_size)[0] for index in range(count)]

            return unpacked_values[0] if count == 1 else unpacked_values

        elif type_ == 5:

            return read_rational(tiff_bytes, value_or_offset, endian)

        elif type_ == 7:

            field_bytes = tiff_bytes[value_or_offset:value_or_offset + count] if total_size > 4 else struct.pack(endian + "I", value_or_offset)[:count]
            return decode(field_bytes)

    except Exception as exception:

        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")

    return None

def read_image_file_directory(tiff_bytes, offset, endian, tag_name_map):

    tag_values = {}

    try:

        entry_count = struct.unpack_from(endian + "H", tiff_bytes, offset)[0]
        offset += 2

        for _ in range(entry_count):

            tag, type_, count, value_or_offset = struct.unpack_from(endian + "HHII", tiff_bytes, offset)
            offset += 12
            tag_name = tag_name_map.get(tag)

            if tag_name:

                value = read_directory_field_value(tiff_bytes, tag, type_, count, value_or_offset, endian)

                if value is not None:

                    tag_values[tag_name] = value

    except Exception as exception:

        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")

    return tag_values

def gps_degrees_minutes_seconds_to_decimal(coordinate_parts, hemisphere_ref):

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

        exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
        print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")
        return None

def read_jpeg(file_path):

    file_bytes = read(file_path)
    properties = {}

    if file_bytes[:2] != b"\xff\xd8":

        return properties

    offset = 2

    while offset < len(file_bytes) - 1:

        if file_bytes[offset] != 0xFF:

            break

        marker = file_bytes[offset + 1]

        if marker in (0xD8, 0xD9):

            offset += 2
            continue

        if offset + 4 > len(file_bytes):

            break

        segment_length = struct.unpack_from(">H", file_bytes, offset + 2)[0]
        segment_data   = file_bytes[offset + 4: offset + 2 + segment_length]

        if marker == 0xE0 and segment_data[:4] == b"JFIF":

            if len(segment_data) >= 9:

                properties["Format"]      = "JFIF"
                properties["JFIFVersion"] = f"{segment_data[5]}.{segment_data[6]:02d}"
                density_unit_byte         = segment_data[7]
                properties["XDensity"]    = struct.unpack_from(">H", segment_data, 8)[0]
                properties["YDensity"]    = struct.unpack_from(">H", segment_data, 10)[0]

                if density_unit_byte == 1:

                    properties["DensityUnit"] = "DPI"

                elif density_unit_byte == 2:

                    properties["DensityUnit"] = "DPCM"

        elif marker == 0xE1 and segment_data[:4] == b"Exif":

            tiff_bytes = segment_data[6:]

            if tiff_bytes[:2] == b"II":

                endian = "<"

            elif tiff_bytes[:2] == b"MM":

                endian = ">"

            else:

                offset += 2 + segment_length

                continue

            main_directory_offset = struct.unpack_from(endian + "I", tiff_bytes, 4)[0]
            main_directory        = read_image_file_directory(tiff_bytes, main_directory_offset, endian, EXIF_TAGS)

            for field_name, value in main_directory.items():

                if field_name == "Orientation":

                    properties[field_name] = ORIENTATION_LABELS.get(value, str(value))

                elif field_name == "ResolutionUnit":

                    properties[field_name] = RESOLUTION_UNITS.get(value, str(value))

                elif field_name not in ("ExifIFD", "GPSIFD"):

                    properties[field_name] = str(value)

            if "ExifIFD" in main_directory:

                exif_directory = read_image_file_directory(tiff_bytes, main_directory["ExifIFD"], endian, EXIF_TAGS)

                for field_name, value in exif_directory.items():

                    if field_name not in properties and field_name != "GPSIFD":

                        properties[field_name] = str(value)

            if "GPSIFD" in main_directory:

                gps_directory = read_image_file_directory(tiff_bytes, main_directory["GPSIFD"], endian, GPS_TAGS)
                latitude      = gps_degrees_minutes_seconds_to_decimal(gps_directory.get("GPSLatitude", ""), gps_directory.get("GPSLatitudeRef", ""))
                longitude     = gps_degrees_minutes_seconds_to_decimal(gps_directory.get("GPSLongitude", ""), gps_directory.get("GPSLongitudeRef", ""))

                if latitude is not None:

                    properties["GPSLatitude"]  = f"{latitude} ({gps_directory.get("GPSLatitudeRef", "")})"

                if longitude is not None:

                    properties["GPSLongitude"] = f"{longitude} ({gps_directory.get("GPSLongitudeRef", "")})"

                if "GPSAltitude" in gps_directory:

                    altitude_reference        = "(below sea level)" if gps_directory.get("GPSAltitudeRef") == 1 else "(above sea level)"
                    properties["GPSAltitude"] = f"{gps_directory["GPSAltitude"]} m {altitude_reference}"

                if "GPSDateStamp" in gps_directory:

                    properties["GPSDate"] = gps_directory["GPSDateStamp"]

        offset += 2 + segment_length

    offset = 2

    while offset < len(file_bytes) - 1:

        if file_bytes[offset] != 0xFF:

            break

        marker = file_bytes[offset + 1]

        if marker in range(0xC0, 0xC4):

            if offset + 9 < len(file_bytes):

                precision                 = file_bytes[offset + 4]
                height                    = struct.unpack_from(">H", file_bytes, offset + 5)[0]
                width                     = struct.unpack_from(">H", file_bytes, offset + 7)[0]
                components                = file_bytes[offset + 9]
                properties["ImageWidth"]  = width
                properties["ImageHeight"] = height
                properties["ColorDepth"]  = f"{precision}-bit"
                properties["Components"]  = {1: "Grayscale", 3: "YCbCr (color)", 4: "CMYK"}.get(components, str(components))

            break

        if marker in (0xD8, 0xD9):

            offset += 2
            continue

        if offset + 4 > len(file_bytes):

            break

        segment_length = struct.unpack_from(">H", file_bytes, offset + 2)[0]
        offset += 2 + segment_length

    return properties

def read_png(file_path):

    file_bytes = read(file_path)
    properties = {}

    if file_bytes[:8] != b"\x89PNG\r\n\x1a\n":

        return properties

    offset = 8

    while offset < len(file_bytes) - 8:

        try:

            chunk_length = struct.unpack_from(">I", file_bytes, offset)[0]
            chunk_type   = file_bytes[offset + 4: offset + 8].decode("ascii", errors="replace")
            chunk_data   = file_bytes[offset + 8: offset + 8 + chunk_length]

            if chunk_type == "IHDR" and chunk_length >= 13:

                properties["ImageWidth"]  = struct.unpack_from(">I", chunk_data, 0)[0]
                properties["ImageHeight"] = struct.unpack_from(">I", chunk_data, 4)[0]
                bit_depth        = chunk_data[8]
                color_type       = chunk_data[9]
                interlaced       = chunk_data[12]
                color_type_labels = {0: "Grayscale", 2: "RGB", 3: "Indexed", 4: "Grayscale+Alpha", 6: "RGBA"}
                properties["ColorType"]  = color_type_labels.get(color_type, str(color_type))
                properties["BitDepth"]   = f"{bit_depth}-bit"
                properties["Interlaced"] = "Yes" if interlaced == 1 else "No"

            elif chunk_type == "tEXt":

                first_null = chunk_data.find(b"\x00")

                if first_null != -1:

                    key   = decode(chunk_data[:first_null])
                    value = decode(chunk_data[first_null + 1:])

                    if key and value:

                        properties[key] = value

            elif chunk_type == "iTXt":

                first_null = chunk_data.find(b"\x00")

                if first_null != -1:

                    key             = decode(chunk_data[:first_null])
                    remaining_bytes = chunk_data[first_null + 1:]
                    second_null     = remaining_bytes.find(b"\x00", 2)

                    if second_null != -1:

                        third_null = remaining_bytes.find(b"\x00", second_null + 1)

                        if third_null != -1:

                            value = decode(remaining_bytes[third_null + 1:])

                            if key and value:

                                properties[key] = value

            elif chunk_type == "pHYs" and chunk_length >= 9:

                pixels_per_unit_x = struct.unpack_from(">I", chunk_data, 0)[0]
                pixels_per_unit_y = struct.unpack_from(">I", chunk_data, 4)[0]
                density_unit_byte = chunk_data[8]

                if density_unit_byte == 1:

                    properties["XResolution"] = f"{round(pixels_per_unit_x * 0.0254)} DPI"
                    properties["YResolution"] = f"{round(pixels_per_unit_y * 0.0254)} DPI"

                else:

                    properties["XResolution"] = f"{pixels_per_unit_x} px/unit"
                    properties["YResolution"] = f"{pixels_per_unit_y} px/unit"

            elif chunk_type == "tIME" and chunk_length >= 7:

                year   = struct.unpack_from(">H", chunk_data, 0)[0]
                month  = chunk_data[2]
                day    = chunk_data[3]
                hour   = chunk_data[4]
                minute = chunk_data[5]
                second = chunk_data[6]
                properties["LastModified"] = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} UTC"

            elif chunk_type == "gAMA" and chunk_length == 4:

                gamma                = struct.unpack_from(">I", chunk_data)[0] / 100000
                properties["Gamma"]  = f"{gamma:.5f}"

            offset += 12 + chunk_length

        except Exception as exception:

            exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
            print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")
            break

    return properties

def read(file_path, file_type):

    if file_type in ("JPEG", "JPG"):

        return read_jpeg(file_path)

    if file_type == "PNG":

        return read_png(file_path)

    return {}