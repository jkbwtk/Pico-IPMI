# universal
TEST_DATA = 00

UPDATE_SYSINFO = 1

GET_SYSINFO = 11
GET_SENSORS = 12
GET_WIFI = 13
GET_POWER_STATUS = 14
GET_HDD_ACTIVITY = 15
GET_MQTT_STATUS = 16
GET_AMBIENT_TEMP = 17

SYSINFO_DATA = 21
SENSOR_DATA = 22
WIFI_DATA = 23
POWER_STATUS_DATA = 24
HDD_ACTIVITY_DATA = 25
MQTT_STATUS_DATA = 26
AMBIENT_TEMP_DATA = 27

COMM_POWER = 50
COMM_RESET = 51
COMM_SLEEP = 52

ENCODER_LEFT = 60
ENCODER_RIGHT = 61
ENCODER_PRESSED = 62

OK = 200
SYSINFO_OK = 201

PING = 66
PONG = 99
PACKET_STOP = b'\0m]X]X]'

# errors
ERR_UNSUPPORTED_OPCODE = 240
ERR_INVALID_DATA = 241
ERR_REQUEST_FAILED = 242

# UART

# MQTT
REGISTER = 160
REGISTRATION_DATA = 161
REGISTERED = 162
