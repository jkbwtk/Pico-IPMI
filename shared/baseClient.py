import struct
from shared.packets import packData, unpackData
from shared.utils import flatten


try:
    from micropython import const  # check if running in micropython
    from shared.utils import time_ns

    del const
except ModuleNotFoundError as e:
    from time import time_ns


class BaseClient:
    def __init__(self, client) -> None:
        self.client = client
        self.requests: dict[int, list] = {}

    def checkRequestRetryCallback(self, request: list):
        raise NotImplementedError

    def checkRequests(self):
        now = time_ns()

        for uniq, request in self.requests.items():
            if now >= request[1] + 3_000_000_000:
                if request[2] >= 3:
                    self.handleFailedRequest(request)
                    try:
                        self.requests.pop(uniq)
                    except KeyError:
                        pass
                    continue

                request[2] += 1
                request[1] = now

                self.checkRequestRetryCallback(request)
                print(f'Request [{uniq}] timed out, retries [{request[2]}]')

    def watchPacket(self, uniq: int, channel: int, packetRaw: bytes) -> None:
        self.requests[uniq] = [uniq, time_ns(), 0, channel, packetRaw]

    def writePacket(self, packet: list, important=False) -> None:
        raise NotImplementedError

        # packetRaw = packData(packet)

        # if important:
        #     self.watchPacket(packet[3], packet[4], packetRaw)

        # self.client.write(packetRaw)

    def checkRX(self) -> None:
        raise NotImplementedError

    def handleRX(self, *args) -> None:
        raise NotImplementedError

    def handleFailedRequest(self, request: list) -> None:
        print(f'Request [{request[0]}] failed, running cleanup')


def genericRXHandler(fn):
    def wrapper(self):
        data = self.readPacket()

        if data is None:
            return

        try:
            packet = unpackData(data)
            fn(self, packet)
        except Exception as e:
            print(e)
            print('[genericRX] Corrupted packet:', data)

    return wrapper


def genericWritePacket(fn):
    def wrapper(self, packet: list, important=False):
        packetRaw = packData(flatten(packet))

        if important:
            self.watchPacket(packet[3], packet[4], packetRaw)

        fn(self, packet, packetRaw)

    return wrapper
