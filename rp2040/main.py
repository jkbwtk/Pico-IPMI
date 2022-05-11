import json
import math
import time

import displayRoutine as display

from machine import PWM, UART, Pin, Timer, ADC
from micropython import const
from shared.baseClient import genericRXHandler
from shared.debouncer import debounce
from shared.opcodes import (
    AMBIENT_TEMP_DATA, COMM_POWER, COMM_RESET, ENCODER_LEFT, ENCODER_PRESSED, ENCODER_RIGHT, GET_AMBIENT_TEMP,
    GET_HDD_ACTIVITY, GET_MQTT_STATUS, GET_POWER_STATUS, GET_SENSORS, GET_SYSINFO, GET_WIFI, HDD_ACTIVITY_DATA,
    MQTT_STATUS_DATA, OK, PING, PONG, POWER_STATUS_DATA, SENSOR_DATA, SYSINFO_DATA, SYSINFO_OK, TEST_DATA,
    UPDATE_SYSINFO, WIFI_DATA)
from shared.routes import ESP, HOST, PICO, PRIVATE
from shared.sensors import parseSensors
from shared.uart import UART as UartBase
from shared.utils import (getHash, getUniq, loadJSON, saveJSON, time_ns,
                          timeDivider)


picoLED = Pin(25, Pin.OUT)
powerSwitch = Pin(27, Pin.OUT, value=1)
resetSwitch = Pin(26, Pin.OUT, value=1)
powerLED = Pin(16, Pin.IN, Pin.PULL_DOWN)
hddLED = Pin(17, Pin.IN, Pin.PULL_DOWN)
buzzer = PWM(Pin(18))
nextButton = Pin(19, Pin.IN, Pin.PULL_UP)
tempSensor = ADC(4)


class State:
    def __init__(self) -> None:
        self.sysInfo = loadJSON('sysInfo.json')
        self.hash = getHash(self.sysInfo)

        self.hostConnected = False
        self.espConnected = False

        self.uartHost = UartHost(self)
        self.uartESP = UartESP(self)

        self.HDDActivity = HDDActivityRecorder()

        self.hostSensorsRequestUniq = None
        self.espMQTTStatusRequestUniq = None

    def fetchSensors(self):
        if self.hostSensorsRequestUniq is None:
            uniq = getUniq()
            self.hostSensorsRequestUniq = uniq
            self.route([GET_SENSORS, PICO, HOST, uniq, PRIVATE], important=True)

    def fetchMQTTStatus(self):
        if self.espConnected:
            if self.espMQTTStatusRequestUniq is None:
                uniq = getUniq()
                self.espMQTTStatusRequestUniq = uniq
                self.route([GET_MQTT_STATUS, PICO, ESP, uniq, PRIVATE], important=True)
        else:
            self.route([GET_MQTT_STATUS, PICO, ESP, getUniq(), PRIVATE], important=False)

    def fetchWiFiSignal(self):
        self.route([GET_WIFI, PICO, ESP, getUniq(), PRIVATE], important=True)

    def connectHost(self):
        if not self.hostConnected:
            print('Connecting to host')
            self.route([GET_SYSINFO, PICO, HOST, getUniq(), PRIVATE, self.hash])

    def route(self, packet: list, important=False) -> bool:
        if packet[2] == PICO:
            return False

        if packet[2] == HOST:
            self.uartHost.writePacket(packet, important)
        else:
            self.uartESP.writePacket(packet, important)

        return True

    def handleRX(self, packet):
        if packet[0] == TEST_DATA:
            print('Test data:', packet[5])
        elif packet[0] == PING:
            self.route([PONG, packet[2], packet[1], packet[3], packet[4]])
        elif packet[0] == UPDATE_SYSINFO:
            if packet[5][0] != self.hash:
                self.uartHost.updateSysInfo()
            else:
                print('Valid sysInfo')
        elif packet[0] == SYSINFO_DATA:
            self.sysInfo = json.loads(packet[5][0])
            saveJSON('sysInfo.json', self.sysInfo)
            self.hash = getHash(self.sysInfo)
            print('Synced sysInfo file')
            self.uartHost.stateConnected()
            self.route([UPDATE_SYSINFO, PICO, ESP, getUniq(), PRIVATE, self.hash], important=True)
        elif packet[0] == SYSINFO_OK:
            print('Valid sysInfo')
            self.uartHost.stateConnected()
        elif packet[0] == SENSOR_DATA:
            self.hostSensorsRequestUniq = None
            if packet[5].pop(0) != self.hash:
                print('Invalid sysInfo hash, resyncing')
                self.uartHost.updateSysInfo()
            else:
                # print(parseSensors(packet[5], self.sysInfo))
                display.updateSensors(parseSensors(packet[5], self.sysInfo))
        elif packet[0] == WIFI_DATA:
            display.updateWiFiSignal(packet[5][0])
        elif packet[0] == MQTT_STATUS_DATA:
            self.uartESP.stateWorking()
            self.espMQTTStatusRequestUniq = None
            display.updateMQTTStatus(packet[5][0])
        elif packet[0] == COMM_POWER:
            powerSwitch.low()
            time.sleep_ms(100)
            powerSwitch.high()

            self.route([
                OK,
                packet[2],
                packet[1],
                packet[3],
                packet[4]
            ])
        elif packet[0] == COMM_RESET:
            resetSwitch.low()
            time.sleep_ms(200)
            resetSwitch.high()

            self.route([
                OK,
                packet[2],
                packet[1],
                packet[3],
                packet[4]
            ])

        elif packet[0] == GET_SYSINFO:
            if len(packet[5]) > 0 and packet[5][0] == self.hash:
                self.route([
                    SYSINFO_OK,
                    packet[2],
                    packet[1],
                    packet[3],
                    PRIVATE
                ])
            else:
                self.route([
                    SYSINFO_DATA,
                    packet[2],
                    packet[1],
                    packet[3],
                    PRIVATE,
                    json.dumps(self.sysInfo)
                ])

        elif packet[0] == GET_POWER_STATUS:
            self.route([
                POWER_STATUS_DATA,
                packet[2],
                packet[1],
                packet[3],
                PRIVATE,
                powerLED.value()
            ])

        elif packet[0] == GET_HDD_ACTIVITY:
            self.route([
                HDD_ACTIVITY_DATA,
                packet[2],
                packet[1],
                packet[3],
                PRIVATE,
                self.HDDActivity.activity
            ])

        elif packet[0] == GET_AMBIENT_TEMP:
            self.route([
                AMBIENT_TEMP_DATA,
                packet[2],
                packet[1],
                packet[3],
                PRIVATE,
                readAmbientTemp()
            ])

        # if packet[1] == HOST and not self.hostConnected:
            # self.uartHost.stateWorking()
        # if packet[1] != HOST and not self.espConnected:
        #     self.uartESP.stateWorking()


class UartHost(UartBase):
    def __init__(self, state: State) -> None:
        uart = UART(0,  baudrate=57600, tx=Pin(0), rx=Pin(1), timeout=0, rxbuf=2048)
        self.state = state

        super().__init__(uart)

    @genericRXHandler
    def handleRX(self, packet: list):
        if self.state.route(packet):
            return

        if self.requests.get(packet[3]) is not None:
            # print('Deleting request:', packet[3])
            self.requests.pop(packet[3])

        self.state.handleRX(packet)

    def updateSysInfo(self):
        self.state.hostSensorsRequestUniq = None
        self.state.hostConnected = False
        display.changeState(display.STATE_CONNECTING)
        self.state.connectHost()

    def stateConnected(self):
        self.state.hostSensorsRequestUniq = None
        self.state.hostConnected = True
        display.changeState(display.STATE_WORKING)
        self.state.fetchSensors()

    def handleFailedRequest(self, request: list) -> None:
        if not self.state.hostConnected:
            return

        super().handleFailedRequest(request)

        self.state.hostSensorsRequestUniq = None
        display.changeState(display.STATE_CONNECTION_LOST)
        display.refresh(None)
        time.sleep(5)
        self.updateSysInfo()


class UartESP(UartBase):
    def __init__(self, state: State) -> None:
        uart = UART(1, baudrate=57600, tx=Pin(4), rx=Pin(5), timeout=0, rxbuf=2048)
        self.state = state

        super().__init__(uart)

    @genericRXHandler
    def handleRX(self, packet: list):
        if self.state.route(packet):
            return

        if self.requests.get(packet[3]) is not None:
            self.requests.pop(packet[3])

        self.state.handleRX(packet)

    def stateWorking(self):
        self.state.espConnected = True
        self.state.espMQTTStatusRequestUniq = None

    def handleFailedRequest(self, request: list) -> None:
        if not self.state.espConnected:
            return

        super().handleFailedRequest(request)

        self.state.espMQTTStatusRequestUniq = None
        self.state.espConnected = False
        display.updateWiFiSignal(0)
        display.updateMQTTStatus(0)


def readAmbientTemp() -> float:
    val = tempSensor.read_u16() * (3.3 / 65536)
    temp = 27 - (val - 0.706) / 0.001721

    return temp


def setupEncoder(state: State):
    btn = Pin(11, Pin.IN)
    left = Pin(12, Pin.IN)
    right = Pin(13, Pin.IN)

    # @debounce(10)
    def leftHandler(_):
        # state.route(Packet(ENCODER_LEFT, PICO, HOST, getUniq(), PRIVATE))
        display.SENSOR_OFFSET += 1

    @debounce(50)
    def rightHandler(_):
        if left.value() == 0:
            return leftHandler(_)

        # state.route(Packet(ENCODER_RIGHT, PICO, HOST, getUniq(), PRIVATE))
        display.SENSOR_OFFSET -= 1

    @debounce(300)
    def btnHandler(_):
        display.toggle()
        # state.route(Packet(ENCODER_PRESSED, PICO, HOST, getUniq(), PRIVATE))

    btn.irq(trigger=Pin.IRQ_FALLING, handler=btnHandler.exec)
    # left.irq(trigger=Pin.IRQ_FALLING, handler=leftHandler.exec)
    right.irq(trigger=Pin.IRQ_FALLING, handler=rightHandler.exec)


right_assist = 0
count = 0  # Rotate the value of the encoder


def setupEncoderV2(state: State):
    right = Pin(13, Pin.IN)
    left = Pin(12, Pin.IN)
    down = Pin(11, Pin.IN)
    timer = Timer()

    def right_handler(pin):
        global right_assist
        right.irq(handler=None)
        right_assist = 1

    def down_handler(pin):
        global count
        down.irq(handler=None)
        count = 0
        print("down", count)
        state.route([ENCODER_PRESSED, PICO, HOST, getUniq(), PRIVATE])
        down.irq(trigger=Pin.IRQ_FALLING, handler=down_handler)

    def loop(_):
        global count, right_assist

        if (right_assist == 1):
            if (left.value() == 1):
                count = count - 1
                print("left",  count)
                state.route([ENCODER_LEFT, PICO, HOST, getUniq(), PRIVATE])

            elif (left.value() == 0):
                count = count + 1
                print("right",  count)
                state.route([ENCODER_RIGHT, PICO, HOST, getUniq(), PRIVATE])

            while (left.value() == 0) | (right.value() == 0):
                time.sleep_ms(1)

            right_assist = 0
            right.irq(trigger=Pin.IRQ_FALLING, handler=right_handler)

    right.irq(trigger=Pin.IRQ_FALLING, handler=right_handler)
    down.irq(trigger=Pin.IRQ_FALLING, handler=down_handler)
    timer.init(freq=1_000, mode=Timer.PERIODIC, callback=loop)


class HDDActivityRecorder:
    def __init__(self):
        self.activity = [0 for _ in range(100)]

    def record(self, value: int):
        self.activity.pop(0)
        self.activity.append(value)


def processHostLEDs(state: State):
    # print('Power LED', powerLED.value())
    # print('HDD LED', hddLED.value())

    # if powerLED.value() == 1:
    #     display.powerOn()
    # else:
    #     display.powerOff()

    state.HDDActivity.record(hddLED.value())


def main():
    LOOP_TIME = const(50)  # ms
    LOOP_COUNTER = 0

    state = State()
    setupEncoder(state)
    # setupEncoderV2(state)

    lastLoopTime = LOOP_TIME
    drift = 0
    avgTime = LOOP_TIME

    try:
        uartHost = state.uartHost
        uartESP = state.uartESP

        uartHost.updateSysInfo()

        while True:
            loopStart = time_ns()

            # blink led
            if timeDivider(LOOP_COUNTER + 1, LOOP_TIME, 1_000):
                picoLED.toggle()

            uartHost.checkRX()
            uartESP.checkRX()

            if timeDivider(LOOP_COUNTER + 1, LOOP_TIME, 1_000):
                if state.hostConnected:
                    state.fetchSensors()
                else:
                    state.connectHost()

            if timeDivider(LOOP_COUNTER, LOOP_TIME, 5_000):
                state.fetchMQTTStatus()
                # print(state.HDDActivity.activity)

            if timeDivider(LOOP_COUNTER, LOOP_TIME, 20_000) and state.espConnected:
                state.fetchWiFiSignal()

            if timeDivider(LOOP_COUNTER, LOOP_TIME, 50):
                uartHost.checkRequests()
                uartESP.checkRequests()

            if timeDivider(LOOP_COUNTER, LOOP_TIME, 100):
                processHostLEDs(state)

            # loop stuff
            LOOP_COUNTER = (LOOP_COUNTER + 1) % 2_147_483_648

            adjustedTime = min(LOOP_TIME * 2, max(0, LOOP_TIME - drift))
            time.sleep_ms(adjustedTime)

            lastLoopTime = math.ceil((time_ns() - loopStart) / 1_000_000)
            lastLoopTime = max(0, lastLoopTime)  # handle overflow

            avgTime = (avgTime * 49 + lastLoopTime) / 50
            drift += lastLoopTime - LOOP_TIME

            # if timeDivider(LOOP_COUNTER, LOOP_TIME, 5_000):
            # print("loop time:", lastLoopTime, "avg:", avgTime, "drift:", drift)

    except KeyboardInterrupt:
        pass


if (nextButton.value() == 0):
    picoLED.on()
else:
    picoLED.off()
    main()
