from ssd1306 import SSD1306_I2C
import framebuf
from machine import I2C, Pin, Timer


SCREEN_UPDATED = False
DISPLAY_STATE = -1
COUNTER = 0

WIFI_SIGNAL = 0
SENSORS = {}


i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
display = SSD1306_I2C(128, 64, i2c)

display.fill(0)
display.contrast(0)

wifi_0 = bytearray([195, 231, 126, 60, 60, 126, 231, 195])
wifi_1 = bytearray([192, 192, 0, 0, 0, 0, 0, 0])
wifi_2 = bytearray([200, 200, 8, 16, 224, 0, 0, 0])
wifi_3 = bytearray([201, 201, 9, 17, 227, 2, 14, 248])
wifi = [wifi_0, wifi_1, wifi_2, wifi_3]

pk_logo = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7f, 0xf8, 0x00, 0x3f, 0xfc, 0x00, 0x1f, 0xfe,
                     0x7f, 0xf8, 0x00, 0x3f, 0xfc, 0x00, 0x1f, 0xfe, 0x7f, 0xf8, 0x00, 0x3f, 0xfc, 0x00, 0x1f, 0xfe,
                     0x7f, 0xf8, 0x00, 0x3f, 0xfc, 0x00, 0x1f, 0xfe, 0x7f, 0xf8, 0x00, 0x3f, 0xfc, 0x00, 0x1f, 0xfe,
                     0x7f, 0xf8, 0x00, 0x3f, 0xfc, 0x00, 0x1f, 0xfe, 0x7f, 0xf8, 0x00, 0x3f, 0xfc, 0x00, 0x1f, 0xfe,
                     0x7f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfe, 0x7f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfe,
                     0x1f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 0x07, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf0,
                     0x63, 0xff, 0xff, 0xfc, 0x3f, 0xff, 0xff, 0xc2, 0x79, 0xff, 0xff, 0xf1, 0x8f, 0xff, 0xff, 0x8e,
                     0x7c, 0xff, 0xff, 0xc7, 0xe3, 0xff, 0xff, 0x3e, 0x7e, 0x7f, 0xff, 0x9f, 0xf9, 0xff, 0xfe, 0x7e,
                     0x6f, 0x3f, 0xff, 0x3d, 0xbc, 0xff, 0xfc, 0xf6, 0x67, 0x9f, 0xfe, 0x79, 0x9e, 0x7f, 0xf9, 0xe6,
                     0x63, 0xcf, 0xfc, 0xf1, 0x8f, 0x3f, 0xf1, 0xc6, 0x61, 0xe7, 0xfd, 0xf1, 0x8f, 0x9f, 0xf3, 0x86,
                     0x60, 0xe7, 0xf9, 0xb1, 0x8d, 0xdf, 0xe7, 0x86, 0x60, 0x73, 0xf3, 0x31, 0x8c, 0xcf, 0xe7, 0x06,
                     0x60, 0x73, 0xf7, 0x31, 0x8c, 0xef, 0xce, 0x06, 0x60, 0x39, 0xe6, 0x31, 0x8c, 0x67, 0xce, 0x06,
                     0x60, 0x38, 0xce, 0x31, 0x8c, 0x77, 0x9c, 0x06, 0x60, 0x1c, 0x8c, 0x31, 0x8c, 0x33, 0x98, 0x06,
                     0x60, 0x1c, 0x18, 0x31, 0x8c, 0x19, 0x38, 0x06, 0x60, 0x0e, 0x1f, 0xff, 0xff, 0xf8, 0x30, 0x06,
                     0x60, 0x0e, 0x1f, 0xff, 0xff, 0xfc, 0x70, 0x06, 0x60, 0x06, 0x38, 0x31, 0x8c, 0x1c, 0x70, 0x06,
                     0x60, 0x06, 0x30, 0x31, 0x8c, 0x1c, 0x60, 0x06, 0x60, 0x07, 0x30, 0x31, 0x8c, 0x0c, 0x60, 0x06,
                     0x60, 0x03, 0x70, 0x31, 0x8c, 0x0e, 0xe0, 0x06, 0x60, 0x03, 0x60, 0x31, 0x8c, 0x06, 0xc0, 0x06,
                     0x60, 0x03, 0xe0, 0x00, 0x00, 0x07, 0xc0, 0x06, 0x60, 0x01, 0xc0, 0x00, 0x00, 0x03, 0x80, 0x06,
                     0x60, 0x01, 0xc0, 0x00, 0x00, 0x03, 0x80, 0x06, 0x7f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfe,
                     0x7f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfe, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02,
                     0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x4f, 0xff, 0xff, 0xc0, 0x7f, 0xc0, 0x3f, 0xf2,
                     0x4f, 0xff, 0xff, 0xf8, 0x7f, 0xc0, 0x7f, 0xf2, 0x4f, 0xfc, 0x1f, 0xfc, 0x7f, 0xc0, 0xff, 0xe2,
                     0x4f, 0xfc, 0x0f, 0xfe, 0x7f, 0xc1, 0xff, 0xc2, 0x4f, 0xfc, 0x07, 0xfe, 0x7f, 0xc3, 0xff, 0x82,
                     0x4f, 0xfc, 0x03, 0xfe, 0x7f, 0xc7, 0xff, 0x02, 0x4f, 0xfc, 0x03, 0xfe, 0x7f, 0xcf, 0xfe, 0x02,
                     0x4f, 0xfc, 0x03, 0xfe, 0x7f, 0xff, 0xfc, 0x02, 0x4f, 0xfc, 0x07, 0xfe, 0x7f, 0xff, 0xf8, 0x02,
                     0x4f, 0xfc, 0x07, 0xfe, 0x7f, 0xff, 0xf0, 0x02, 0x4f, 0xfc, 0x0f, 0xfe, 0x7f, 0xff, 0xf0, 0x02,
                     0x4f, 0xfc, 0x3f, 0xfc, 0x7f, 0xff, 0xf8, 0x02, 0x4f, 0xff, 0xff, 0xf8, 0x7f, 0xcf, 0xfc, 0x02,
                     0x4f, 0xff, 0xff, 0xf0, 0x7f, 0xc7, 0xfe, 0x02, 0x4f, 0xff, 0xff, 0xc0, 0x7f, 0xc3, 0xff, 0x02,
                     0x4f, 0xfc, 0x00, 0x00, 0x7f, 0xc1, 0xff, 0x82, 0x4f, 0xfc, 0x00, 0x00, 0x7f, 0xc0, 0xff, 0xc2,
                     0x4f, 0xfc, 0x00, 0x00, 0x7f, 0xc0, 0x7f, 0xe2, 0x4f, 0xfc, 0x00, 0x00, 0x7f, 0xc0, 0x3f, 0xf2,
                     0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02,
                     0x7f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

custom = bytearray([])


def horizCenter(text: str, y: int, color: int):
    pad = 64 - (len(text) * 4)
    display.text(text, pad, y, color)


def updateWiFiSignal(level: int):
    global WIFI_SIGNAL, SCREEN_UPDATED
    WIFI_SIGNAL = level % len(wifi)
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
    # horizCenter('???', 28, 1)
    frame = framebuf.FrameBuffer(pk_logo, 64, 64, framebuf.MONO_HLSB)
    display.blit(frame, 32, 0, 0)


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
    frame = framebuf.FrameBuffer(wifi[WIFI_SIGNAL], 8, 8, framebuf.MONO_VLSB)
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


refresh(-1)
timer = Timer()
timer.init(freq=.5, mode=Timer.PERIODIC, callback=refresh)
