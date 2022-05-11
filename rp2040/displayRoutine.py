import time
from ssd1306 import SSD1306_I2C
import framebuf
from machine import I2C, Pin, Timer
import bmpParser as bmp


SCREEN_ACTIVE = False
DISPLAY_STATE = -1
COUNTER = 0

WIFI_SIGNAL = 0
MQTT_STATUS = 0
SENSORS = {}

SENSOR_OFFSET = 0


# freq(260_000_000)
# print('Changed cpu freq to {} Mhz'.format(freq() // 1_000_000))
i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=400_000)
display = SSD1306_I2C(128, 64, i2c)
timer = Timer()

display.fill(0)
display.contrast(0)

t1 = time.ticks_ms()
graphics = bmp.loadJSONGraphics('graphics.json')
t2 = time.ticks_ms()
print('Graphics loaded in:', time.ticks_diff(t2, t1), 'ms')

custom = bytearray([])


def forceRefresh(fn):
    def wrapper(*args, **kwargs):
        fn(*args, **kwargs)
        refresh(-1)

    return wrapper


def toggle():
    global SCREEN_ACTIVE, timer

    SCREEN_ACTIVE = not SCREEN_ACTIVE

    if not SCREEN_ACTIVE:
        timer.deinit()
        display.fill(0)
        display.show()
    else:
        refresh(-1)
        timer.init(freq=5, mode=Timer.PERIODIC, callback=refresh)


def powerOff():
    if SCREEN_ACTIVE:
        toggle()


def powerOn():
    if not SCREEN_ACTIVE:
        toggle()


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


def updateMQTTStatus(status: int):
    global MQTT_STATUS, SCREEN_UPDATED
    MQTT_STATUS = status % len(graphics.get('mqtt'))


def updateSensors(sensors: dict):
    global SENSORS
    SENSORS = sensors


def updateCustomImage(image: bytearray):
    global custom
    custom = image


@forceRefresh
def changeState(state: int):
    global DISPLAY_STATE
    DISPLAY_STATE = state


def stateIdle():
    pk_logo = graphics.get('pk_logo')
    centeredImage(pk_logo)


def stateConnecting():
    global COUNTER

    drawWiFi()
    drawMQTT()

    horizCenter('Syncing', 17, 1)
    horizCenter('With Host', 27, 1)
    display.text('.' * (COUNTER % 4), 52, 37, 1)


def stateConnectionLost():
    display.fill(0)

    drawWiFi()
    drawMQTT()

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


def drawMQTT():
    mqtt = graphics.get('mqtt')[MQTT_STATUS]
    frame = framebuf.FrameBuffer(
        bytearray(mqtt[2]), mqtt[0], mqtt[1], framebuf.MONO_HLSB)
    display.blit(frame, 120, 10, 0)


def drawBar(val: int, minn: int, maxx: int, x: int, y: int, width: int, height: int, orientation: int, color: int):
    if val < minn:
        return

    if val > maxx:
        val = maxx

    val = (val - minn) / (maxx - minn)

    if orientation == 0:
        val = int(val * width)
        display.fill_rect(x, y, val, height, color)
    elif orientation == 1:
        val = int(val * height)
        display.fill_rect(x, y, width, val, color)
    elif orientation == 2:
        val = int(val * width)
        display.fill_rect(x + (width - val), y, val, height, color)
    elif orientation == 3:
        val = int(val * height)
        display.fill_rect(x, y + (height - val), width, val, color)


def drawSensors():
    global SENSOR_OFFSET

    if SENSORS == {}:
        return

    pages = 2

    if SENSOR_OFFSET % pages == 1:
        cpus = len(SENSORS['cpus'])
        barWidth = int(120 / cpus)

        horizCenter(f'{cpus} CPUs', 0, 1)
        horizCenter(f'Total: {SENSORS.get("cpu_usage", -1):.0f}%', 10, 1)

        for i, v in enumerate(SENSORS['cpus']):
            drawBar(v, 0, 100, i * barWidth, 20, barWidth, 44, 3, 1)

    elif SENSOR_OFFSET % pages == 0:
        display.text(f'CPU: {SENSORS.get("cpu_usage", -1)}%', 0, 0, 1)
        display.text(f'CPU: {SENSORS.get("cpu_temp", -1)}C', 0, 9, 1)
        display.text(f'CPU: {SENSORS.get("cpu_power", -1)}W', 0, 18, 1)
        display.text(f'RAM: {SENSORS.get("ram_used", -1)}MB', 0, 27, 1)
        display.text(f'RAM: {SENSORS.get("ram_freq", -1)}MHz', 0, 36, 1)

        if (SENSORS['gpus'] != 0):
            display.text(f'GPU: {SENSORS["gpus"][0].get("usage", -1)}%', 0, 45, 1)
            display.text(f'GPU: {SENSORS["gpus"][0].get("temp", -1)}C', 0, 54, 1)
        else:
            display.text(f'FAN: {SENSORS.get("cpu_fan", -1)}RPM'.format(), 0, 45, 1)
            display.text(f'BATT: {SENSORS.get("batt_level", -1)}%'.format(), 0, 54, 1)


def stateWorking():
    drawWiFi()
    drawMQTT()
    drawSensors()


STATE_CONNECTING = 0
STATE_CONNECTION_LOST = 1
STATE_WORKING = 2
STATE_CUSTOM_PICTURE = 50
STATE_IDLE = -1


def refresh(timer):
    global COUNTER, DISPLAY_STATE, SCREEN_ACTIVE

    if not SCREEN_ACTIVE:
        return

    display.fill(0)

    if DISPLAY_STATE == STATE_CONNECTING:
        stateConnecting()
    elif DISPLAY_STATE == STATE_CONNECTION_LOST:
        stateConnectionLost()
    elif DISPLAY_STATE == STATE_WORKING:
        stateWorking()
    elif DISPLAY_STATE == STATE_CUSTOM_PICTURE:
        stateCustomPicture()
    else:
        stateIdle()

    COUNTER = (COUNTER % 65_535) + 1
    display.show()


toggle()

t1 = time.ticks_ms()
refresh(-1)
t2 = time.ticks_ms()
print('Frame presented in:', time.ticks_diff(t2, t1), 'ms')
