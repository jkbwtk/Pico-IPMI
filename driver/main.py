import json
import time
import winreg
import serial.tools.list_ports
import serial
from driver.sensors import getSensors, getSysInfo
from shared.baseClient import genericRXHandler
from shared.opcodes import ENCODER_LEFT, ENCODER_PRESSED, ENCODER_RIGHT, GET_SENSORS, GET_SYSINFO, PING, PONG, SENSOR_DATA, SYSINFO_DATA, SYSINFO_OK, UPDATE_SYSINFO
from shared.uart import UART as UartBase
from shared.utils import getHash, getUniq, timeDivider
from shared.routes import HOST, PICO, PRIVATE

import win32api
import win32con


def press(*args):
    '''
    one press, one release.
    accepts as many arguments as you want. e.g. press('left_arrow', 'a','b').
    '''
    for i in args:
        win32api.keybd_event(i, 0, 0, 0)
        time.sleep(.001)
        win32api.keybd_event(i, 0, win32con.KEYEVENTF_KEYUP, 0)


def findCOMPort():
    for port in serial.tools.list_ports.comports():
        if 'CP210x' in port.description:
            return port.device


reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
key = winreg.OpenKey(reg, 'SOFTWARE\\HWiNFO64\\VSB')


class State:
    def __init__(self) -> None:
        self.sysInfo = getSysInfo()
        self.hash = getHash(self.sysInfo)

        self.sensors = getSensors()
        self.sensorsTimestamp = time.time_ns()

        self.uartHost = UartHost(self)

    def getSensors(self):
        # if time.time_ns() > self.sensorsTimestamp + 1_000_000_000:
        #     self.sensors = getSensors()
        #     self.sensorsTimestamp = time.time_ns()

        # return self.sensors
        return getSensors()


class UartHost(UartBase):
    def __init__(self, state: State) -> None:
        uart = waitForSerialClient()
        self.state = state

        super().__init__(uart)

    def route(self, packet: list) -> bool:
        if packet[2] == HOST:
            return False

        self.state.uartHost.writePacket(packet)
        return True

    @genericRXHandler
    def handleRX(self, packet: list):
        print(packet)

        if self.route(packet):
            return

        if packet[0] == GET_SYSINFO:
            if packet[5][0] == self.state.hash:
                self.writePacket([
                    SYSINFO_OK,
                    packet[2],
                    packet[1],
                    packet[3],
                    PRIVATE
                ])
            else:
                self.writePacket([
                    SYSINFO_DATA,
                    packet[2],
                    packet[1],
                    packet[3],
                    PRIVATE,
                    json.dumps(self.state.sysInfo)
                ])
        elif packet[0] == GET_SENSORS:
            self.writePacket([
                SENSOR_DATA,
                packet[2],
                packet[1],
                packet[3],
                PRIVATE,
                self.state.hash,
                *self.state.getSensors().values(),
            ])
        elif packet[0] == PING:
            if packet[5][0] == self.state.hash:
                self.writePacket([
                    PONG,
                    packet[2],
                    packet[1],
                    packet[3],
                    PRIVATE
                ])
            else:
                self.writePacket([
                    UPDATE_SYSINFO,
                    packet[2],
                    packet[1],
                    packet[3],
                    PRIVATE
                ])

        elif packet[0] == ENCODER_LEFT:
            press(0xAF)
        elif packet[0] == ENCODER_RIGHT:
            press(0xAE)
        elif packet[0] == ENCODER_PRESSED:
            press(0xAD)


def waitForConnection():
    while (port := findCOMPort()) is None:
        time.sleep(1)
        print('Waiting for port...')

    return port


def waitForSerialClient():
    while True:
        try:
            client = serial.Serial(
                waitForConnection(),
                baudrate=57600,
                timeout=0
            )

            if client.isOpen():
                return client
        except serial.SerialException as e:
            print(e)

        print('Waiting for connection...')
        time.sleep(1)


def reconnectSerial(client: UartHost):
    port = waitForConnection()

    while True:
        try:
            client.client.setPort(port)

            if client.client.isOpen():
                return

            client.client.open()

        except serial.SerialException as e:
            print(e)

        print('Waiting for reconnection...')
        time.sleep(1)


def main():
    LOOP_TIME = 1  # ms
    LOOP_COUNTER = 0

    state = State()
    state.uartHost.writePacket([UPDATE_SYSINFO, HOST, PICO, getUniq(), PRIVATE, state.hash])

    try:
        uartHost = state.uartHost

        while True:
            try:
                uartHost.checkRX()

                if timeDivider(LOOP_COUNTER, LOOP_TIME, 50):
                    uartHost.checkRequests()

                LOOP_COUNTER = (LOOP_COUNTER + 1) % 2_147_483_648
                time.sleep(LOOP_TIME / 1000)
            except serial.SerialException as e:
                print(f'Adapter disconnected: {e}')
                reconnectSerial(uartHost)
                print(f'Reconnected on port {uartHost.client.port}')

    except KeyboardInterrupt:
        pass


main()
