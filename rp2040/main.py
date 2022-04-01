import json
import math
import struct
import time

from machine import UART, Pin, Timer
from utime import sleep_ms

import displayRoutine as display

TEST_DATA = 00
SENSOR_DATA = 11
CONFIG_DATA = 12
WIFI_DATA = 13

GET_CONFIG = 1
UPDATE_CONFIG = 2
GET_SENSORS = 3
GET_WIFI = 4

COMM_POWER = 50
COMM_RESET = 51

PING = 66
PONG = 99
PACKET_STOP = b'\0m]X]X]'


wifi_1 = bytearray([192, 192, 0, 0, 0, 0, 0, 0])
wifi_2 = bytearray([200, 200, 8, 16, 224, 0, 0, 0])
wifi_3 = bytearray([201, 201, 9, 17, 227, 2, 14, 248])
wifi = [wifi_1, wifi_2, wifi_3]


def loadConfig():
    file = open('sensors.json', 'r', encoding='utf-8')
    data: dict[str, dict] = json.load(file)  # type: ignore
    file.close()

    return data


def saveConfig(data: str):
    file = open('sensors.json', 'w', encoding='utf-8')

    file.write(data)

    file.close()


def unpackDataOld(packet, config: dict[str, dict]):
    data = {}
    packetFormat = ''

    for name, sensor in sorted(config.items()):
        valueType = sensor['type']
        packetFormat += valueType

    rawData = struct.unpack(packetFormat, packet)
    i = 2

    for name, sensor in sorted(config.items()):
        data[name] = rawData[i]
        i += 1

    return data


def unpackData(packet):
    # print(packet)
    opcode = packet[0]
    headerSize = int(packet[2:packet.find(b's')])
    header = packet[1:headerSize + 1].decode()
    data = struct.unpack(header, packet[:-len(PACKET_STOP)])

    # print('Opcode', opcode)
    # print('Header Size', headerSize)
    # print('Header', header)
    # print('Data', data)

    return data


def packData(opcode: int, packetFormat: str, *data):
    HEADER_SIZE = len(packetFormat) + 2
    HEADER_SIZE += math.floor(math.log10(HEADER_SIZE)) + 1
    packetFormat = 'B{}s'.format(HEADER_SIZE) + packetFormat

    print(packetFormat)
    header = bytearray(packetFormat, encoding='utf-8')
    packet = struct.pack(packetFormat, opcode, header, *data)

    return packet + PACKET_STOP


def parseSensorData(data, config):
    sensorData = {}
    i = 2

    for name, sensor in sorted(config.items()):
        sensorData[name] = data[i]
        i += 1

    return sensorData


def printData(data: dict, config: dict[str, dict]):
    for name, value in sorted(data.items()):
        sensor = config[name]
        fullName = sensor['name']
        unit = sensor['unit']

        print('{}: {} {}'.format(fullName, value, unit))


def createRequest(request):
    packetFormat = 'B3s'
    header = bytearray(packetFormat)

    return struct.pack(packetFormat, request, header) + PACKET_STOP


led = Pin(25, Pin.OUT)
uart0 = UART(0, baudrate=19200, tx=Pin(0), rx=Pin(
    1), timeout_char=10, timeout=1000, parity=0, rxbuf=2048)
uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(
    5), timeout_char=10, timeout=1000, parity=0, rxbuf=2048)
relay1 = Pin(22, Pin.OUT)
relay2 = Pin(21, Pin.OUT)

relay1.high()
relay2.high()


def readLine(uart: UART):
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


def updateConfig(UART0_WORKING_FLAG):
    while not UART0_WORKING_FLAG:
        try:
            uart0.write(createRequest(GET_CONFIG))

            packet = uart0.readline()
            if packet == None:
                raise Exception

            data = unpackData(packet)
            if data[0] == CONFIG_DATA:
                config = json.loads(data[2])
                saveConfig(data[2])
            else:
                continue

            UART0_WORKING_FLAG = True
        except:
            print('Host is unresponsive')
            time.sleep(5)


UART0_HEARTBEAT_COUNTER = 0
UART0_WORKING_FLAG = False
UART0_WRITING = False
UART0_BACKOFF = 0


UART1_HEARTBEAT_COUNTER = 0
UART1_WORKING_FLAG = False
UART1_WRITING = False
UART1_BACKOFF = 0


def fetchSensors(timer):
    global UART0_WRITING
    global UART0_HEARTBEAT_COUNTER
    global UART0_WORKING_FLAG

    if UART0_WORKING_FLAG and not UART0_WRITING:
        UART0_WRITING = True
        uart0.write(createRequest(GET_SENSORS))
        UART0_WRITING = False

        UART0_HEARTBEAT_COUNTER += 1

        if UART0_HEARTBEAT_COUNTER > 5:
            UART0_WORKING_FLAG = False
            print('Lost connection with host')
            display.changeState(1)


def fetchWiFi(timer):
    global UART1_WRITING
    global UART1_HEARTBEAT_COUNTER
    global UART1_WORKING_FLAG

    if UART1_WORKING_FLAG and not UART1_WRITING:
        UART1_WRITING = True
        uart1.write(createRequest(GET_WIFI))
        UART1_WRITING = False

        UART1_HEARTBEAT_COUNTER += 1

        if UART1_HEARTBEAT_COUNTER > 5:
            UART1_WORKING_FLAG = False
            print('Lost connection with Wi-Fi module')
            display.updateWiFiSignal(0)


def heartBeat(timer):
    led.toggle()
    global UART0_WRITING
    global UART0_HEARTBEAT_COUNTER
    global UART0_WORKING_FLAG

    if UART0_WORKING_FLAG:
        UART0_WRITING = True
        uart0.write(createRequest(PING))
        UART0_WRITING = False

        UART0_HEARTBEAT_COUNTER += 1

        if UART0_HEARTBEAT_COUNTER > 5:
            UART0_WORKING_FLAG = False
            print('Lost connection with host')
            display.changeState(1)


config = {}
SHBTMR = Timer()
WIFIHBTMR = Timer()

SHBTMR.init(freq=1 / 2, mode=Timer.PERIODIC, callback=fetchSensors)
WIFIHBTMR.init(freq=1 / 5, mode=Timer.PERIODIC, callback=fetchWiFi)


while True:
    while uart0.any() > 0:
        # print(uart0.any())
        packet = readLine(uart0)
        if not packet:
            continue

        try:
            data = unpackData(packet)

            if data[0] == SENSOR_DATA:
                # printData(parseSensorData(data, config), config)
                display.updateSensors(parseSensorData(data, config))
                UART0_HEARTBEAT_COUNTER = 0
            elif data[0] == CONFIG_DATA:
                config = json.loads(data[2])
                saveConfig(data[2])
                print('Synced config file')
                display.changeState(2)
                UART0_WORKING_FLAG = True
            elif data[0] == UPDATE_CONFIG:
                UART0_WORKING_FLAG = False
            elif data[0] == PONG:
                UART0_HEARTBEAT_COUNTER = 0
        except Exception as e:
            print(e)
            print('Corrupted packet:', packet)

    while uart1.any() > 0:
        # print(uart1.any())
        packet = readLine(uart1)
        if not packet:
            continue

        try:
            data = unpackData(packet)
            print(data)

            if data[0] == WIFI_DATA:
                display.updateWiFiSignal(data[2])
                UART1_HEARTBEAT_COUNTER = 0
                UART1_WORKING_FLAG = True
            elif data[0] == COMM_POWER:
                relay1.low()
                sleep_ms(100)
                relay1.high()
            elif data[0] == COMM_RESET:
                relay2.low()
                sleep_ms(100)
                relay2.high()

        except Exception as e:
            print(e)
            print('Corrupted packet:', packet)

    if not UART0_WORKING_FLAG and UART0_BACKOFF == 0:
        print('Syncing config file')
        display.changeState(0)

        UART0_WRITING = True
        uart0.write(createRequest(GET_CONFIG))
        UART0_WRITING = False

    if not UART1_WORKING_FLAG and UART1_BACKOFF == 0:
        print('Connecting to Wi-Fi module')
        UART1_WRITING = True
        uart1.write(createRequest(GET_WIFI))
        UART1_WRITING = False

    UART0_BACKOFF = (UART0_BACKOFF + 1) % 50
    UART1_BACKOFF = (UART1_BACKOFF + 1) % 50
    time.sleep_ms(100)
