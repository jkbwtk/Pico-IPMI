import json
import time
from shared.sensors import parseSensors

from machine import UART, Pin, Timer
from shared.opcodes import COMM_POWER, COMM_RESET, GET_SENSORS, GET_SYSINFO, GET_WIFI, PONG, SENSOR_DATA, SYSINFO_DATA, SYSINFO_OK, UPDATE_SYSINFO, WIFI_DATA
from shared.packets import createRequest, packDataAuto, unpackData
from shared.uart import readLine
from shared.utils import getHash, loadJSON, saveJSON
from utime import sleep_ms

import displayRoutine as display



led = Pin(25, Pin.OUT)
uart0 = UART(0, baudrate=38400, tx=Pin(0), rx=Pin(1), timeout=1000, rxbuf=2048)
uart1 = UART(1, baudrate=38400, tx=Pin(4), rx=Pin(5), timeout=1000, rxbuf=2048)
relay1 = Pin(22, Pin.OUT)
relay2 = Pin(21, Pin.OUT)

relay1.high()
relay2.high()


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
    global UART0_BACKOFF

    if UART0_WORKING_FLAG and not UART0_WRITING:
        UART0_WRITING = True
        uart0.write(createRequest(GET_SENSORS))
        UART0_WRITING = False

        UART0_HEARTBEAT_COUNTER += 1

        if UART0_HEARTBEAT_COUNTER > 5:
            UART0_WORKING_FLAG = False
            print('Lost connection with host')
            display.changeState(1)
            UART0_BACKOFF = 1


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


sysInfo = loadJSON('sysInfo.json')
hash = getHash(sysInfo)

rawSensorsPacket = b''

LOOP_TIME = 1
SHBTMR = Timer()
WIFIHBTMR = Timer()

time.sleep(2)
SHBTMR.init(freq=1 / 2, mode=Timer.PERIODIC, callback=fetchSensors)
WIFIHBTMR.init(freq=1 / 10, mode=Timer.PERIODIC, callback=fetchWiFi)


while True:
    while uart0.any() > 0:
        # print(uart0.any())
        packet = readLine(uart0)
        if not packet:
            continue

        try:
            data = unpackData(packet)

            if data[0] == SENSOR_DATA:
                if data[-1] != hash:
                    uart0.write(packDataAuto(GET_SYSINFO, hash))
                    UART0_HEARTBEAT_COUNTER = 0
                else:
                    display.updateSensors(parseSensors(data, sysInfo))
                    rawSensorsPacket = packet
                    UART0_HEARTBEAT_COUNTER = 0
            elif data[0] == SYSINFO_DATA:
                sysInfo = json.loads(data[2])
                saveJSON('sysInfo.json', data[2])
                hash = getHash(sysInfo)
                print('Synced sysInfo file')
                display.changeState(2)
                UART0_WORKING_FLAG = True
                UART0_HEARTBEAT_COUNTER = 0
            elif data[0] == UPDATE_SYSINFO:
                if data[2] != hash:
                    UART0_WORKING_FLAG = False
                    UART0_BACKOFF = 0
                else:
                    print('Valid sysInfo')
                    UART0_WORKING_FLAG = True
                    UART0_HEARTBEAT_COUNTER = 0
                    display.changeState(2)
            elif data[0] == SYSINFO_OK:
                UART0_WORKING_FLAG = True
                print('Valid sysInfo')
                display.changeState(2)
                UART0_HEARTBEAT_COUNTER = 0
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
                sleep_ms(200)
                relay2.high()
            elif data[0] == GET_SENSORS:
                print(rawSensorsPacket)
                uart1.write(rawSensorsPacket)

        except Exception as e:
            print(e)
            print('Corrupted packet:', packet)

    if not UART0_WORKING_FLAG and UART0_BACKOFF == 0:
        print('Syncing sysInfo')
        display.changeState(0)

        UART0_WRITING = True
        uart0.write(packDataAuto(GET_SYSINFO, hash))
        UART0_WRITING = False

    if not UART1_WORKING_FLAG and UART1_BACKOFF == 0:
        print('Connecting to Wi-Fi module')
        UART1_WRITING = True
        uart1.write(createRequest(GET_WIFI))
        UART1_WRITING = False

    UART0_BACKOFF = (UART0_BACKOFF + 1) % ((1000 // LOOP_TIME) * 5)
    UART1_BACKOFF = (UART1_BACKOFF + 1) % ((1000 // LOOP_TIME) * 5)
    time.sleep_ms(LOOP_TIME)
