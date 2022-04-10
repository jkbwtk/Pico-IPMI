from machine import UART
import time
import network
import time
from shared.opcodes import COMM_POWER, COMM_RESET, GET_SENSORS, GET_WIFI, SENSOR_DATA, WIFI_DATA
from shared.packets import createRequest, packDataAuto, unpackData
from shared.uart import readLine
from shared.utils import loadJSON
import ubinascii
from umqtt.simple import MQTTClient
import machine


def connectToWifi(wlan, name, password):
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(name, password)
        while not wlan.isconnected():
            pass


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
    elif power > - 70:
        return 2
    else:
        return 1


def main():
    uart = UART(0, baudrate=38400, timeout=5000, rxbuf=2048)
    wlan = network.WLAN(network.STA_IF)
    client_id = ubinascii.hexlify(machine.unique_id())

    settings = loadJSON('settings.json')
    connectToWifi(wlan, settings['wifi']['name'], settings['wifi']['password'])
    mqtt = MQTTClient(client_id, settings['mqtt']['ip'], user=settings['mqtt']['login'], password=settings['mqtt']['password'], keepalive=60)


    def sub_cb(topic, msg):
        print((topic, msg))

        if msg == b'power':
            uart.write(createRequest(COMM_POWER))
        elif msg == b'reset':
            uart.write(createRequest(COMM_RESET))
        elif msg == b'getSensors':
            uart.write(createRequest(GET_SENSORS))


    mqtt.set_callback(sub_cb)
    mqtt.connect()
    mqtt.subscribe(b"pico_in")

    MQTT_BACKOFF = 0
    LOOP_TIME = 1


    while True:
        while uart.any() > 0:
            packet = readLine(uart)
            if not packet:
                continue

            try:
                data = unpackData(packet)

                if data[0] == GET_WIFI:
                    signal = getSignalPower(wlan)
                    translated = translateSignalPower(signal)

                    print('Signal:', signal, 'Translated:', translated)
                    packet = packDataAuto(WIFI_DATA, translated)
                    uart.write(packet)
                elif data[0] == SENSOR_DATA:
                    mqtt.publish(b'pico_out', packet)

            except Exception as e:
                print(e)
                print('Corrupted packet:', packet)

        mqtt.check_msg()

        if MQTT_BACKOFF == 0:
            mqtt.ping()

        MQTT_BACKOFF = (MQTT_BACKOFF + 1) % ((1000 // LOOP_TIME) * 5)
        time.sleep_ms(LOOP_TIME)


if not FLASH_MODE:
    main()