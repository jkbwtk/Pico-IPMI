from shared.opcodes import PACKET_STOP
import math
import struct


# fix for esp8266
def log10(number):
    # check for log10 support
    try:
        return math.log10(number)
    except AttributeError:
        return math.log(number) / math.log(10)


def packData(opcode: int, packetFormat: str, *data):
    headerSize = len(packetFormat) + 2
    headerSize += math.floor(log10(headerSize)) + 1
    packetFormat = 'B{}s'.format(headerSize) + packetFormat

    # print(packetFormat)
    header = bytearray(packetFormat, 'utf-8')
    packet = struct.pack(packetFormat, opcode, header, *data)

    return packet + PACKET_STOP


def packDataAuto(opcode: int, *data):
    packetFormat = ''

    for i, d in enumerate(data):
        t = type(d)

        if t == float:
            packetFormat += 'f'
        elif t == int:
            if d < 256 and d >= 0:
                packetFormat += 'B'
            else:
                packetFormat += 'i'
        elif t == bool:
            packetFormat += 'h'
        else:
            packetFormat += f'{len(d)}s'

    return packData(opcode, packetFormat, *data)


def unpackData(packet):
    opcode = packet[0]
    headerSize = int(packet[2:packet.find(b's')])
    header = packet[1:headerSize + 1].decode()
    data = struct.unpack(header, packet[:-len(PACKET_STOP)])

    # print('Opcode', opcode)
    # print('Header Size', headerSize)
    # print('Header', header)
    # print('Data', data)

    return data


def createRequest(request):
    return packData(request, '')
