import json

import ubinascii
from machine import UART, unique_id
from shared.baseClient import genericRXHandler
from shared.mqtt import MQTT as MQTTBase
from shared.opcodes import (GET_MQTT_STATUS, GET_SYSINFO, GET_WIFI,
                            MQTT_STATUS_DATA, PING, PONG, REGISTER, REGISTERED,
                            REGISTRATION_DATA, SYSINFO_DATA, SYSINFO_OK,
                            UPDATE_SYSINFO, WIFI_DATA)
from shared.packets import unpackData
from shared.routes import COMM, ESP, PICO, PRIVATE, PUBLIC
from shared.uart import UART as UartBase
from shared.utils import getHash, getUniq, loadJSON
from wifi_init import wlan
from umqtt.simple import MQTTClient


def getSignalPower():
    if not wlan.isconnected():
        return 0

    networks = wlan.scan()
    name = wlan.config('essid')

    for n in networks:
        if name == n[0].decode():
            return n[3]

    return 0


def translateSignalPower(power: int):
    if power == 0:
        return 0
    elif power > -50:
        return 3
    elif power > - 70:
        return 2
    else:
        return 1


class State:
    def __init__(self):
        self.clientID = ubinascii.hexlify(unique_id())

        self.sysInfo = {}
        self.hash = getHash(self.sysInfo)

        self.settings = loadJSON('settings.json')

        self.commRegistered = False
        self.picoConnected = False

        self.uartPico = UartPico(self)
        self.mqttComm = MQTTComm(self)

        self.commPingUniq = None
        self.picoPingUniq = None

    def registerComm(self):
        if not self.commRegistered:
            print('Registering to comm')
            self.route([REGISTRATION_DATA, ESP, COMM, getUniq(), PUBLIC, self.clientID, json.dumps(self.sysInfo)])

    def connectPico(self):
        if not self.picoConnected:
            print('Connecting to pico')
            self.route([GET_SYSINFO, ESP, PICO, getUniq(), PRIVATE, self.hash])

    def pingComm(self):
        if self.commPingUniq is None:
            uniq = getUniq()
            self.commPingUniq = uniq
            self.route([PING, ESP, COMM, uniq, PRIVATE], important=True)

    def pingPico(self):
        if self.picoPingUniq is None:
            uniq = getUniq()
            self.picoPingUniq = uniq
            self.route([PING, ESP, PICO, uniq, PRIVATE], important=True)

    def route(self, packet: list, important=False) -> bool:
        if packet[2] == ESP:
            return False

        if packet[2] == COMM:
            self.mqttComm.writePacket(packet, important)
        else:
            self.uartPico.writePacket(packet, important)

        return True

    def handleRX(self, packet: list):
        print(packet)

        if packet[0] == PING:
            self.route([PONG, packet[2], packet[1], packet[3], packet[4]])
        elif packet[0] == PONG:
            print('Received pong')

            if packet[1] == COMM:
                self.commPingUniq = None
            elif packet[1] == PICO:
                self.picoPingUniq = None

            print('Processed pong')
        elif packet[0] == GET_WIFI:
            print('Reading WiFi power...')
            power = translateSignalPower(getSignalPower())
            print('WiFi power:', power)

            self.route([
                WIFI_DATA,
                packet[2],
                packet[1],
                packet[3],
                PRIVATE,
                power
            ])

            print('Sent WiFi power')
        elif packet[0] == GET_MQTT_STATUS:
            self.route([
                MQTT_STATUS_DATA,
                packet[2],
                packet[1],
                packet[3],
                PRIVATE,
                self.commRegistered
            ])
        elif packet[0] == REGISTER:
            self.mqttComm.regegister()
        elif packet[0] == REGISTERED:
            print('Registered to comm')
            self.mqttComm.stateRegistered()

        elif packet[0] == UPDATE_SYSINFO:
            if packet[5][0] != self.hash:
                self.uartPico.updateSysInfo()
            else:
                print('Valid sysInfo')
        elif packet[0] == SYSINFO_DATA:
            self.sysInfo = json.loads(packet[5][0])
            self.hash = getHash(self.sysInfo)
            print('Synced sysInfo file')
            self.uartPico.stateConnected()
            self.route([UPDATE_SYSINFO, ESP, COMM, getUniq(), PRIVATE, self.hash], important=True)
        elif packet[0] == SYSINFO_OK:
            print('Valid sysInfo')
            self.uartPico.stateConnected()


class UartPico(UartBase):
    def __init__(self, state: State) -> None:
        uart = UART(0, baudrate=57600, rxbuf=2048)
        self.state = state

        super().__init__(uart)

    @genericRXHandler
    def handleRX(self, packet: list):
        if self.state.route(packet):
            return

        if self.requests.get(packet[3]) is not None:
            self.requests.pop(packet[3])

        self.state.handleRX(packet)

    def updateSysInfo(self):
        self.state.picoConnected = False
        self.state.picoPingUniq = None
        self.state.connectPico()

    def stateConnected(self):
        self.state.picoConnected = True
        self.state.picoPingUniq = None

    def handleFailedRequest(self, request: list) -> None:
        if not self.state.picoConnected:
            return

        super().handleFailedRequest(request)

        self.state.picoPingUniq = None
        self.updateSysInfo()


class MQTTComm(MQTTBase):
    def __init__(self, state: State) -> None:
        mqtt = MQTTClient(
            state.clientID,
            state.settings['mqtt']['ip'],
            user=state.settings['mqtt']['login'],
            password=state.settings['mqtt']['password'],
            keepalive=60
        )
        self.state = state

        super().__init__(mqtt)

    def handleRX(self, topic, msg: bytes):
        try:
            packet = unpackData(msg)

            if self.state.route(packet):
                return

            if self.requests.get(packet[3]) is not None:
                self.requests.pop(packet[3])

            self.state.handleRX(packet)
        except Exception as e:
            print(e)
            print('[MQTT RX] Corrupted packet:', msg)

    def regegister(self):
        self.state.commRegistered = False
        self.state.commPingUniq = None

    def stateRegistered(self):
        self.state.commRegistered = True
        self.state.commPingUniq = None

    def handleFailedRequest(self, request: list) -> None:
        if not self.state.commRegistered:
            return

        super().handleFailedRequest(request)

        self.state.commPingUniq = None
        self.regegister()
