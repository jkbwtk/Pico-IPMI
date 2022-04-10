import json
import time
import winreg

import serial
from shared.opcodes import GET_SENSORS, GET_SYSINFO, PING, PONG, SENSOR_DATA, SYSINFO_DATA, SYSINFO_OK, UPDATE_SYSINFO
from shared.packets import createRequest, packDataAuto, unpackData
from shared.uart import readLine
from shared.utils import getHash

from driver.sensors import getSensors, getSysInfo


def findCOMPort():
    raise NotImplementedError()


LOOP_TIME = 1  # ms

reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
key = winreg.OpenKey(reg, 'SOFTWARE\\HWiNFO64\\VSB')

uart = serial.Serial('COM5', baudrate=38400, timeout=0.01)

sysInfo = getSysInfo()
hash = getHash(sysInfo)


uart.read_all()  # flush system buffer
uart.write(packDataAuto(UPDATE_SYSINFO, hash))

while True:
    while uart.in_waiting > 0:
        try:
            packet = readLine(uart)
            if not packet:
                continue

            data = unpackData(packet)
            print(data)

            if data[0] == GET_SYSINFO:
                if data[2] == hash:
                    uart.write(createRequest(SYSINFO_OK))
                else:
                    uart.write(packDataAuto(SYSINFO_DATA, json.dumps(sysInfo).encode('utf-8')))
            elif data[0] == GET_SENSORS:
                uart.write(packDataAuto(SENSOR_DATA, *getSensors().values(), hash))
            elif data[0] == PING:
                uart.write(createRequest(PONG))
        except Exception as e:
            print(e)

    time.sleep(LOOP_TIME / 1000)
