import binascii
import json
from hashlib import sha256


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

    print(type(data))
    if type(data) == str:
        file.write(data)
    elif type(data) == bytes:
        file.write(data.decode('utf-8'))
    else:
        file.write(json.dumps(data))

    file.close()


def getHash(data: dict) -> str:
    hasher = sha256()

    for k in sorted(data.keys()):
        hasher.update(json.dumps(data[k]).encode('utf-8'))


    hash = binascii.hexlify(hasher.digest())

    return hash[:6]


def parseType(value: str):
    try:
        v = float(value)

        if v == v // 1:
            return int(v)
        else:
            return v
    except:
        if value == 'No':
            return False
        elif value == 'Yes':
            return True

        return value


def sortKeys(data: dict) -> dict:
    d = {}

    for k in sorted(data):
        d[k] = data[k]


    return d
