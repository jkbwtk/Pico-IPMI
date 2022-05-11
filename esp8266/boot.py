# This file is executed on every boot (including wake-boot from deepsleep)
import wifi_init
import gc

import esp
import uos
import webrepl
from machine import Pin
from network import AP_IF, WLAN

esp.osdebug(None)

button = Pin(16, Pin.IN)
led = Pin(2, Pin.OUT, value=1)
FLASH_MODE = False

if button.value() == 0:
    led.value(0)
    FLASH_MODE = True
else:
    led.value(1)
    uos.dupterm(None, 1)

# disable access point
ap = WLAN(AP_IF)
ap.active(False)

webrepl.start()

del uos
del esp
del button
del led
del Pin
del ap

gc.collect()

wifi_init.main()
