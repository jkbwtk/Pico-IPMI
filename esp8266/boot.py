# This file is executed on every boot (including wake-boot from deepsleep)
import machine
import uos
import webrepl
import gc
from network import WLAN, AP_IF
import esp
esp.osdebug(None)
uos.dupterm(None, 1)

# disable access point
ap = WLAN(AP_IF)
ap.active(False)

webrepl.start()
gc.collect()
