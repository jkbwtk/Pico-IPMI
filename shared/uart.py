from shared.baseClient import BaseClient, genericWritePacket
from shared.opcodes import PACKET_STOP


try:
    from micropython import const  # check if running in micropython
    from shared.utils import time_ns

    del const
except ModuleNotFoundError as e:
    from time import time_ns


class UART(BaseClient):
    def checkRequestRetryCallback(self, request: list):
        self.client.write(request[4])

    @genericWritePacket
    def writePacket(self, _, packetRaw: bytes):
        self.client.write(packetRaw)

    def readPacket(self) -> bytes | None:
        buffer = b''
        startTime = time_ns()

        while len(buffer) <= 1024:
            packet: bytes | None = self.client.read(1)
            if packet is None:
                if len(buffer) == 0:
                    return None

                if time_ns() > startTime + 50_000_000:
                    print(f'Packet timeout, buffer [{buffer}]')
                    return None

                continue

            buffer += packet
            startTime = time_ns()

            if not buffer.endswith(PACKET_STOP):
                continue

            return buffer

        raise Exception('Packet size exceeded 1024 bytes')

    def checkRX(self) -> None:
        if hasattr(self.client, 'any'):
            while self.client.any() > 0:
                self.handleRX()
        else:
            while self.client.in_waiting > 0:
                self.handleRX()

    def handleRX(self, *args) -> None:
        raise NotImplementedError
