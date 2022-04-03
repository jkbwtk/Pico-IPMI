import time
from ssd1306 import SSD1306_I2C
import framebuf
from machine import I2C, Pin, Timer, freq
import bmpParser as bmp


SCREEN_UPDATED = False
DISPLAY_STATE = -1
COUNTER = 0

WIFI_SIGNAL = 0
SENSORS = {}


# freq(260_000_000)
# print('Changed cpu freq to {} Mhz'.format(freq() // 1_000_000))
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
display = SSD1306_I2C(128, 64, i2c)

display.fill(0)
display.contrast(0)

t1 = time.ticks_ms()
graphics = bmp.loadJSONGraphics('graphics.json')
t2 = time.ticks_ms()
print('Graphics loaded in:', time.ticks_diff(t2, t1), 'ms')

custom = bytearray([])


def horizCenter(text: str, y: int, color: int):
    pad = 64 - (len(text) * 4)
    display.text(text, pad, y, color)


def centeredImage(image: tuple):
    frame = framebuf.FrameBuffer(
        bytearray(image[2]), image[0], image[1], framebuf.MONO_HLSB)
    padX = (128 - image[0]) // 2
    padY = (64 - image[1]) // 2

    display.blit(frame, padX, padY, 0)


def updateWiFiSignal(level: int):
    global WIFI_SIGNAL, SCREEN_UPDATED
    WIFI_SIGNAL = level % len(graphics.get('wifi'))
    SCREEN_UPDATED = True


def updateSensors(sensors: dict):
    global SENSORS
    SENSORS = sensors


def updateCustomImage(image: bytearray):
    global custom
    custom = image


def changeState(state: int):
    global DISPLAY_STATE
    DISPLAY_STATE = state


def stateIdle():
    pk_logo = graphics.get('pk_logo')
    centeredImage(pk_logo)


def stateConnecting():
    global COUNTER

    horizCenter('Syncing', 17, 1)
    horizCenter('Config File', 27, 1)
    display.text('.' * (COUNTER % 4), 52, 37, 1)


def stateConnectionLost():
    display.fill(0)

    if COUNTER % 10 > 4:
        display.fill_rect(28, 5, 8, 40, 1)
        display.fill_rect(28, 50, 8, 8, 1)

    display.text('LOST', 45, 13, 1)
    display.text('CONNECTION', 45, 25, 1)
    display.text('WITH HOST', 45, 38, 1)

    display.show()


def stateCustomPicture():
    display.fill(0)

    frame = framebuf.FrameBuffer(custom, 128, 64, framebuf.MONO_HLSB)
    display.blit(frame, 0, 0, 0)


def drawWiFi():
    wifi = graphics.get('wifi')[WIFI_SIGNAL]
    frame = framebuf.FrameBuffer(
        bytearray(wifi[2]), wifi[0], wifi[1], framebuf.MONO_HLSB)
    display.blit(frame, 120, 0, 0)


def drawSensors():
    display.text('CPU: {}%'.format(SENSORS.get('cpu_usage', -1)), 0, 0, 1)
    display.text('CPU: {}C'.format(SENSORS.get('cpu_temp', -1)), 0, 9, 1)
    display.text('CPU: {}W'.format(SENSORS.get('cpu_power', -1)), 0, 18, 1)
    display.text('RAM: {}MB'.format(SENSORS.get('ram_used', -1)), 0, 27, 1)
    display.text('GPU: {}%'.format(SENSORS.get('gpu_usage', -1)), 0, 36, 1)
    display.text('GPU: {}C'.format(SENSORS.get('gpu_temp', -1)), 0, 45, 1)
    display.text('GPU: {}W'.format(SENSORS.get('gpu_power', -1)), 0, 54, 1)


def stateWorking():
    drawWiFi()
    drawSensors()


def refresh(timer):
    global COUNTER, DISPLAY_STATE
    display.fill(0)

    if DISPLAY_STATE == 0:
        stateConnecting()
    elif DISPLAY_STATE == 1:
        stateConnectionLost()
    elif DISPLAY_STATE == 2:
        stateWorking()
    elif DISPLAY_STATE == 50:
        stateCustomPicture()
    else:
        stateIdle()

    COUNTER = (COUNTER % 65_536) + 1
    display.show()


t1 = time.ticks_ms()
refresh(-1)
t2 = time.ticks_ms()
print('Frame presented in:', time.ticks_diff(t2, t1), 'ms')

timer = Timer()
timer.init(freq=5, mode=Timer.PERIODIC, callback=refresh)
