from machine import UART
import struct
import time
import math
import network
import time
import ubinascii
from umqtt.simple import MQTTClient
import machine


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


def log10(number):
    return math.log(number) / math.log(10)


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


def packData(opcode: int, packetFormat: str, *data):
    HEADER_SIZE = len(packetFormat) + 2
    HEADER_SIZE += math.floor(log10(HEADER_SIZE)) + 1
    packetFormat = 'B{}s'.format(HEADER_SIZE) + packetFormat

    print(packetFormat)
    header = bytearray(packetFormat, 'utf-8')
    packet = struct.pack(packetFormat, opcode, header, *data)

    return packet + PACKET_STOP


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


def createRequest(request):
    packetFormat = 'B3s'
    header = bytearray(packetFormat)

    return struct.pack(packetFormat, request, header) + PACKET_STOP


def getSignalPower(wlan):
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
    elif power > - 80:
        return 2
    else:
        return 1


uart = UART(0, baudrate=9600, timeout=5000, parity=0)
wlan = network.WLAN(network.STA_IF)
client_id = ubinascii.hexlify(machine.unique_id())


def sub_cb(topic, msg):
    print((topic, msg))

    if msg == b'power':
        uart.write(createRequest(COMM_POWER))
    elif msg == b'reset':
        uart.write(createRequest(COMM_RESET))


counter = 0

uart.read()
c = MQTTClient(client_id, 'localhost', keepalive=60)
c.set_callback(sub_cb)
c.connect()
c.subscribe(b"pico")
# print(getSignalPower(wlan))

while True:
    while uart.any() > 0:
        packet = readLine(uart)
        if not packet:
            continue

        try:
            data = unpackData(packet)
            print(data)

            if data[0] == GET_WIFI:
                signal = getSignalPower(wlan)
                translated = translateSignalPower(signal)

                print('Signal:', signal, 'Translated:', translated)
                packet = packData(WIFI_DATA, 'i', translated)
                uart.write(packet)

        except Exception as e:
            print(e)
            print('Corrupted packet:', packet)

    c.check_msg()
    time.sleep_ms(100)