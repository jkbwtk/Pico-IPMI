import json
import math
import struct
import time
import winreg

import serial
import yaml


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


def loadConfig():
    file = open('sensors.yml', 'r', encoding='utf-8')
    data: dict[str, dict] = yaml.safe_load(file)  # type: ignore
    file.close()

    return data


def convertJSON(data: dict[str, dict]):
    file = open('sensors.json', 'w', encoding='utf-8')

    conv = json.dumps(data)
    file.write(conv)

    file.close()


def rekeyConfig(data: dict[str, dict]):
    newData = {}

    for name, sensor in data.items():
        newName = 'ValueRaw{}'.format(sensor['id'])
        newSensor = sensor.copy()
        newSensor['rawName'] = name

        newData[newName] = newSensor

    return newData


def parseDefault(t: str):
    ints = 'bBhHiIlLqQnN'
    floats = 'efd'

    if t == 'c':
        return '?'
    elif ints.find(t) != -1:
        return 0
    elif t == '?':
        return False
    elif floats.find(t) != -1:
        return 0.0
    elif t.endswith('s'):
        return '?'
    else:
        return -1


def readSensors(key: winreg.HKEYType, conf: dict[str, dict]):
    data = {}
    sensIndex = rekeyConfig(conf)

    for n in range(1024):
        try:
            name, value, _ = winreg.EnumValue(key, n)
            sensor = sensIndex.get(name)

            if sensor != None:
                sensorName = sensor['rawName']
                sensorType = type(parseDefault(sensor['type']))

                if sensorType == str:
                    data[sensorName] = value
                elif sensorType == int:
                    data[sensorName] = int(value)
                elif sensorType == float:
                    data[sensorName] = float(value)

        except:
            break

    return data


def readLine(uart: serial.Serial):
    firstLoop = True
    buffer = b''

    while True:
        packet: bytes = uart.read_until(PACKET_STOP)
        if len(packet) == 0:
            if firstLoop:
                return False

            firstLoop = False
            continue

        buffer += packet
        if not buffer.endswith(PACKET_STOP):
            continue

        return buffer


def printSensors(data: dict, config: dict[str, dict]):
    for name, value in sorted(data.items()):
        sensor = config[name]
        fullName = sensor['name']
        unit = sensor['unit']

        print('{}: {} {}'.format(fullName, value, unit))


def packSensors(data, config: dict[str, dict]):
    dataList = []
    packetFormat = ''

    for name, sensor in sorted(config.items()):
        valueType = sensor['type']
        packetFormat += valueType

        dataList.append(data.get(name, parseDefault(valueType)))

    HEADER_SIZE = len(packetFormat) + 2
    HEADER_SIZE += math.floor(math.log10(HEADER_SIZE)) + 1
    packetFormat = 'B{}s'.format(HEADER_SIZE) + packetFormat

    print(packetFormat)
    header = bytearray(packetFormat, encoding='utf-8')
    packet = struct.pack(packetFormat, SENSOR_DATA, header, *dataList)

    return packet + PACKET_STOP


def packConf(config):
    configJSON = json.dumps(config)
    packetFormat = '{}s'.format(len(configJSON))

    HEADER_SIZE = len(packetFormat) + 2
    HEADER_SIZE += math.floor(math.log10(HEADER_SIZE)) + 1
    packetFormat = 'B{}s'.format(HEADER_SIZE) + packetFormat

    print(packetFormat)
    header = bytearray(packetFormat, encoding='utf-8')
    data = bytearray(configJSON, encoding='utf-8')
    packet = struct.pack(packetFormat, CONFIG_DATA, header, data)

    return packet + PACKET_STOP


def packData(opcode: int, packetFormat: str, *data):
    HEADER_SIZE = len(packetFormat) + 2
    HEADER_SIZE += math.floor(math.log10(HEADER_SIZE)) + 1
    packetFormat = 'B{}s'.format(HEADER_SIZE) + packetFormat

    print(packetFormat)
    header = bytearray(packetFormat, encoding='utf-8')
    packet = struct.pack(packetFormat, opcode, header, *data)

    return packet + PACKET_STOP


def unpackData(packet):
    # print(packet)
    opcode = packet[0]
    headerSize = int(packet[2:packet.find(b's')])
    header = packet[1:headerSize + 1].decode(encoding='utf-8')
    data = struct.unpack(header, packet[:-len(PACKET_STOP)])

    # print('Opcode', opcode)
    # print('Header Size', headerSize)
    print('Header', header)
    # print('Data', data)

    return data


def createRequest(request):
    packetFormat = 'B3s'
    header = bytearray(packetFormat, encoding='utf-8')

    return struct.pack(packetFormat, request, header) + PACKET_STOP


reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
key = winreg.OpenKey(reg, 'SOFTWARE\\HWiNFO64\\VSB')

uart = serial.Serial('COM5', baudrate=19200, timeout=0.01,
                     parity=serial.PARITY_EVEN)


config = loadConfig()
# convertJSON(config)
LOOP_TIME = 1

uart.read_all()  # flush system buffer
uart.write(createRequest(UPDATE_CONFIG))


while True:
    while uart.in_waiting > 0:
        try:
            packet = readLine(uart)
            if not packet:
                continue

            data = unpackData(packet)
            # print(data)

            if data[0] == GET_CONFIG:
                uart.write(packConf(config))
            elif data[0] == GET_SENSORS:
                sensorData = readSensors(key, config)
                # printData(sensorData, config)
                sensorPacket = packSensors(sensorData, config)
                uart.write(sensorPacket)
                # print(sensorPacket)
            elif data[0] == PING:
                uart.write(createRequest(PONG))
        except Exception as e:
            print(e)

    time.sleep(LOOP_TIME / 1000)
