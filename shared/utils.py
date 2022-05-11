import time
import binascii
import json
from hashlib import sha256
from random import getrandbits


def loadJSON(name: str) -> dict:
    try:
        file = open(name, 'r', encoding='utf-8')
        data: dict = json.load(file)  # type: ignore
        file.close()
    except:
        return {}

    return data


def saveJSON(name: str, data):
    file = open(name, 'w', encoding='utf-8')

    if type(data) == str:
        file.write(data)
    elif type(data) == bytes:
        file.write(data.decode('utf-8'))
    else:
        file.write(json.dumps(data))

    file.close()


def getHash(data: dict) -> bytes:
    hasher = sha256()

    for k in sorted(data.keys()):
        hasher.update(json.dumps(data[k]).encode('utf-8'))

    return binascii.hexlify(hasher.digest())[:6]


def parseType(value: str):
    try:
        v = float(value)

        if v == v // 1:
            return int(v)

        return v
    except ValueError:
        if value == 'No':
            return False
        if value == 'Yes':
            return True

        return value


def sortKeys(data: dict) -> dict:
    d = {}

    for k in sorted(data):
        d[k] = data[k]

    return d


def getUniq() -> str:
    return getrandbits(32) % (65535 + 1)


def time_ns() -> int:
    return time.ticks_us() * 1000


def timeDivider(counter: int, loopTime: int, interval: int) -> bool:
    if loopTime > interval:
        return True

    return True if counter % (interval // loopTime) == 0 else False


def flatten(l: list) -> list:
    r = []

    for i in l:
        if isinstance(i, list):
            r += flatten(i)
        else:
            r.append(i)

    return r
