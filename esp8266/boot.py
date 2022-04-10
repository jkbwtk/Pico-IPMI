# This file is executed on every boot (including wake-boot from deepsleep)
from machine import Pin
import uos
import webrepl
import gc
from network import WLAN, AP_IF
import esp
esp.osdebug(None)

button = Pin(16, Pin.IN)
led = Pin(2, Pin.OUT, value=1)


if button.value() == 0:
  led.value(0)
else:
  led.value(1)
  uos.dupterm(None, 1)

# disable access point
ap = WLAN(AP_IF)
ap.active(False)

webrepl.start()
gc.collect()
