import struct
import common
import tables

def ID3v1(field_bytes):

    return field_bytes.split(b'\x00')[0].decode('latin1', errors='replace').strip()

def read(file_path, file_type):

    file_bytes = read(file_path)
    properties = {}

    if file_bytes[:3] == b'ID3':

        version_major            = file_bytes[3]
        version_minor            = file_bytes[4]
        properties['ID3Version'] = f'2.{version_major}.{version_minor}'
        id3_tag_size      = ((file_bytes[6] & 0x7F) << 21 | (file_bytes[7] & 0x7F) << 14 | (file_bytes[8] & 0x7F) << 7  | (file_bytes[9] & 0x7F))
        id3_bytes         = file_bytes[10: 10 + id3_tag_size]
        frame_label_map   = ID3v2_FRAMES_v22 if version_major == 2 else ID3v2_FRAMES_v24
        frame_id_size     = 3 if version_major == 2 else 4
        frame_size_length = 3 if version_major == 2 else 4
        frame_offset = 0

        while frame_offset < len(id3_bytes) - (frame_id_size + frame_size_length + 2):

            frame_id = id3_bytes[frame_offset: frame_offset + frame_id_size].decode('ascii', errors='replace')

            if not frame_id.strip('\x00') or frame_id[0] == '\x00':

                break

            if version_major == 2:

                frame_size = (id3_bytes[frame_offset+3] << 16) | (id3_bytes[frame_offset+4] << 8) | id3_bytes[frame_offset+5]
                frame_data = id3_bytes[frame_offset + 6: frame_offset + 6 + frame_size]
                frame_offset    += 6 + frame_size

            else:

                if version_major == 4:

                    frame_size = ((id3_bytes[frame_offset+4] & 0x7F) << 21 | (id3_bytes[frame_offset+5] & 0x7F) << 14 | (id3_bytes[frame_offset+6] & 0x7F) << 7  | (id3_bytes[frame_offset+7] & 0x7F))

                else:

                    frame_size = struct.unpack_from('>I', id3_bytes, frame_offset + 4)[0]

                frame_data = id3_bytes[frame_offset + 10: frame_offset + 10 + frame_size]
                frame_offset    += 10 + frame_size

            frame_label = frame_label_map.get(frame_id)

            if frame_label and frame_data:

                text_encoding = frame_data[0] if frame_data else 0
                frame_text    = frame_data[1:]

                if frame_id == 'COMM' and len(frame_text) > 3:

                    frame_text = frame_text[3:]

                try:

                    if text_encoding == 0:

                        value = frame_text.decode('latin1', errors='replace')

                    elif text_encoding == 1:

                        value = frame_text.decode('utf-16', errors='replace')

                    elif text_encoding == 2:

                        value = frame_text.decode('utf-16-be', errors='replace')

                    else:

                        value = frame_text.decode('utf-8', errors='replace')

                    value = value.strip('\x00').strip()

                    if value:

                        properties[frame_label] = value

                except Exception as exception:

                    exception_string    = str(exception).split("]")[-1].strip() if "]" in str(exception) else str(exception)
                    print(f"==> {RED}ERROR{RESET}: {exception_string.upper()}")

    if len(file_bytes) >= 128 and file_bytes[-128:-125] == b'TAG':

        tag = file_bytes[-128:]

        for field_name, field_bytes in [('Title',  tag[3:33]),  ('Artist', tag[33:63]), ('Album',  tag[63:93]), ('Year',   tag[93:97])]:

            if field_name not in properties:

                value = ID3v1(field_bytes)

                if value:

                    properties[field_name] = value

        genre = tag[127]

        if 'Genre' not in properties and genre < len(ID3v1_GENRES):

            properties['Genre'] = ID3v1_GENRES[genre]

    return {field_name: value for field_name, value in properties.items() if value}