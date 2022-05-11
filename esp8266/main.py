import gc
import math
import time
from esp8266 import State
from shared.mqttUtils import PUBLIC_IN, picoIn
from shared.utils import time_ns, timeDivider
from machine import Pin


led = Pin(2, Pin.OUT, value=1)


def main():
    LOOP_TIME = 250  # ms
    LOOP_COUNTER = 0

    state = State()

    lastLoopTime = LOOP_TIME
    drift = 0
    # avgTime = LOOP_TIME

    try:
        state.uartPico.updateSysInfo()

        state.mqttComm.client.set_callback(state.mqttComm.handleRX)
        state.mqttComm.client.connect()
        state.mqttComm.client.subscribe(PUBLIC_IN)
        state.mqttComm.client.subscribe(picoIn(state.clientID))
        state.mqttComm.regegister()

        while True:
            loopStart = time_ns()

            # blink led
            if timeDivider(LOOP_COUNTER + 1, LOOP_TIME, 1_000):
                led.value(not led.value())

            # print('Checking messages...', gc.mem_free())
            state.uartPico.checkRX()
            # print('Checking MQTT...', gc.mem_free())
            state.mqttComm.checkRX()

            # if timeDivider(LOOP_COUNTER, LOOP_TIME, 50):
            #     print('Free RAM:', gc.mem_free())
            #     gc.collect()

            # print('Pinging...', gc.mem_free())
            if timeDivider(LOOP_COUNTER + 1, LOOP_TIME, 5_000):
                print('Pinging... MQTT')
                state.mqttComm.client.ping()

                if state.commRegistered:
                    print('Pinging COM...')
                    state.pingComm()

                if state.picoConnected:
                    print('Pinging PICO...')
                    state.pingPico()
                else:
                    state.connectPico()

                if state.picoConnected and not state.commRegistered:
                    state.registerComm()

            print('Checking requests...', gc.mem_free())
            if timeDivider(LOOP_COUNTER, LOOP_TIME, 50):
                state.uartPico.checkRequests()
                state.mqttComm.checkRequests()

            # loop stuff
            print('Looping...', gc.mem_free())
            LOOP_COUNTER = (LOOP_COUNTER + 1) % 2_147_483_648

            adjustedTime = min(LOOP_TIME * 2, max(0, LOOP_TIME - drift))

            if adjustedTime > 500 or adjustedTime < -500:
                print(adjustedTime)

            time.sleep_ms(adjustedTime)

            lastLoopTime = math.ceil((time_ns() - loopStart) / 1_000_000)
            lastLoopTime = max(0, lastLoopTime)  # handle overflow
            drift += lastLoopTime - LOOP_TIME

            print('Requests:', len(state.uartPico.requests), len(state.mqttComm.requests))

    except KeyboardInterrupt:
        pass


print('Free RAM:', gc.mem_free())
gc.collect()

if not FLASH_MODE:
    main()
