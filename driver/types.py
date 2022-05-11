class Packet:
    def __init__(self, opcode: int, origin: int, destination: int, uniq: int, channel: int, *data):
        self.opcode = opcode  # 0
        self.origin = origin  # 1
        self.destination = destination  # 2
        self.uniq = uniq  # 3
        self.channel = channel  # 4
        self.data = list(data)  # 5

    def __str__(self):
        return f'Packet(opcode={self.opcode}, origin={self.origin}, destination={self.destination}, uniq={self.uniq}, channel={self.channel}, data={self.data})'

    def __repr__(self):
        return self.__str__()


class Request:
    def __init__(self, uniq: int, timestamp: int, retries: int, channel: int, packet: bytes):
        self.uniq = uniq  # 0
        self.timestamp = timestamp  # 1
        self.retries = retries  # 2
        self.channel = channel  # 3
        self.packet = packet  # 4

    def __str__(self):
        return f'Request(uniq={self.uniq}, timestamp={self.timestamp}, retries={self.retries}, channel={self.channel}, packet={self.packet})'

    def __repr__(self):
        return self.__str__()
