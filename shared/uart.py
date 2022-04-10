from shared.opcodes import PACKET_STOP


def readLine(uart):
    firstLoop = True
    buffer = b''

    while True:
        packet: bytes | None = uart.read(1)
        if packet == None:
            if firstLoop:
                return False

            firstLoop = False
            continue

        buffer += packet
        if not buffer.endswith(PACKET_STOP):
            continue

        return buffer
