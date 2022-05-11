import time
from network import STA_IF, WLAN, AP_IF
from shared.utils import loadJSON


wlan = WLAN(STA_IF)


def connectToWifi(name, password):
    wlan.active(True)
    retries = 0

    if not wlan.isconnected():
        wlan.connect(name, password)
        while not wlan.isconnected():
            time.sleep(1)
            retries += 1

            if retries > 20:
                return False

    return True


def main():
    settings = loadJSON('settings.json')

    try:
        if not connectToWifi(settings['wifi']['name'], settings['wifi']['password']):
            raise Exception('Failed to connect to wifi')
    except Exception:
        ap = WLAN(AP_IF)
        ap.active(True)

        ap.config(
            essid='ESP RECOVERY',
            authmode=3,
            password='esprecovery'
        )
        ap.ifconfig((
            '192.168.0.1',
            '255.255.255.0',
            '192.168.0.1',
            '1.1.1.1'
        ))

    del settings
