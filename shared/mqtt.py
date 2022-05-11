from shared.baseClient import BaseClient, genericWritePacket
from shared.mqttUtils import PUBLIC_OUT, picoOut
from shared.routes import PUBLIC


class MQTT(BaseClient):
    def checkRequestRetryCallback(self, request: list):
        channel = PUBLIC_OUT if request[3] == PUBLIC else picoOut(self.client.client_id)
        self.client.publish(channel, request[4])

    @genericWritePacket
    def writePacket(self, packet: list, packetRaw: bytes):
        channel = PUBLIC_OUT if packet[4] == PUBLIC else picoOut(self.client.client_id)
        self.client.publish(channel, packetRaw)

    def checkRX(self) -> None:
        self.client.check_msg()

    def handleRX(self, *args) -> None:
        raise NotImplementedError
