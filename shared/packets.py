from shared.opcodes import PACKET_STOP
import struct


def packDataRaw(packetFormat: str, data: list):
    headerSize = len(packetFormat) + 1
    headerSize += len(str(headerSize))

    # fix for sizes 11, 101, 102, 1001, 1002, 1003, etc.
    while headerSize < len(f'{headerSize}s' + packetFormat):
        headerSize += 1

    packetFormat = f'{headerSize}s' + packetFormat

    header = bytearray(packetFormat, 'utf-8')
    packet = struct.pack(packetFormat, header, *data)

    return packet + PACKET_STOP


def packData(data: list):
    packetFormat = ''

    for i, d in enumerate(data):
        t = type(d)

        if t == float:
            packetFormat += 'f'
        elif t == int:
            if d < 256 and d >= 0:
                packetFormat += 'B'
            elif d < 127 and d >= -128:
                packetFormat += 'b'
            elif d < 65536 and d >= 0:
                packetFormat += 'H'
            elif d < 32768 and d >= -32768:
                packetFormat += 'h'
            else:
                packetFormat += 'i'
        elif t == bool:
            packetFormat += 'h'
        else:
            if t == str:
                data[i] = data[i].encode('utf-8')

            packetFormat += f'{len(d)}s'

    return packDataRaw(packetFormat, data)


def unpackDataRaw(packet) -> tuple:
    headerSize = int(packet[0:packet.find(b's')])
    header = packet[0:headerSize].decode('utf-8')
    data = struct.unpack(header, packet[:-len(PACKET_STOP)])

    # print('Opcode', opcode)
    # print('Header Size', headerSize)
    # print('Header', header)
    # print('Data', data)

    return data


def unpackData(packet: bytes) -> list:
    data = unpackDataRaw(packet)

    if len(data) < 6:
        raise Exception('Invalid packet, too few arguments')

    if not isinstance(data[1], int):
        raise Exception('Invalid packet, opcode is not an int')
    if not isinstance(data[2], int):
        raise Exception('Invalid packet, origin is not an int')
    if not isinstance(data[3], int):
        raise Exception('Invalid packet, destination is not an int')
    if not isinstance(data[4], int):
        raise Exception('Invalid packet, uniq is not an int')
    if not isinstance(data[5], int):
        raise Exception('Invalid packet, channel is not an int')

    return [data[1], data[2], data[3], data[4], data[5], list(data[6:])]
