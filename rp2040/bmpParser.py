import math
import os
import re as regex

MAXBANKSIZE = 4
VLSB = 0
HLSB = 1


def readShort(file) -> int:
    return int.from_bytes(file.read(2), 'little')


def readInt(file) -> int:
    return int.from_bytes(file.read(4), 'little')


def reverseColor(b: bytes):
    i = int.from_bytes(b, 'little')
    return (255 - i).to_bytes(1, 'little')


def reverseBits(b: bytes):
    i = int.from_bytes(b, 'little')
    return int('{:08b}'.format(i)[::-1], 2).to_bytes(1, 'little')


def calculateBankSize(pixelBanks, headPos):
    for s in reversed(range(1, MAXBANKSIZE + 1)):
        if pixelBanks - headPos >= s:
            return s


def bytesToInt(s: bytes):
    return int.from_bytes(s, 'little')


def parseWindowsBMP(filename, type: int):
    file = open(filename, "rb")
    file.read(10)
    offset = readInt(file)

    file.read(4)

    width = readInt(file)
    height = readInt(file)

    file.seek(offset)

    readout: list[list[bytes]] = []
    scanline: list[bytes] = []
    headPos = 0
    pixelBanks = math.ceil(width / 8)

    for y in range(height):
        headPos = 0
        scanline = []

        while headPos < pixelBanks:
            bankSize = calculateBankSize(pixelBanks, headPos)
            headPos += bankSize

            for _ in range(bankSize):
                scanline.append(file.read(1))

            file.read(MAXBANKSIZE - bankSize)

        readout.insert(0, scanline.copy())

    file.close()

    if type == HLSB:
        return (width, height, [bytesToInt(bank) for line in readout for bank in line])

    hlsb = [[bytesToInt(bank) for bank in line] for line in readout]
    vlsb = [[0 for _ in range(width)]
            for _ in range(math.ceil(height / 8))]

    for x in range(width):
        for y in range(height):
            vlsb[math.floor(y / 8)][x] = vlsb[math.floor(y / 8)][x] | (
                (hlsb[y][math.floor(x / 8)] & (1 << (7 - (x % 8)))) != 0) << (y % 8)

    return (width, height, [bank for line in vlsb for bank in line])


def loadGraphics(dir: str) -> dir:
    animMatcher = regex.compile(r'^(.*)_(\d+)$')
    graphics = {}

    for filename in os.listdir(dir):
        if filename.endswith(".bmp"):
            name = filename[:-4]

            if animMatcher.match(name):
                animName = animMatcher.match(name).group(1)
                if animName not in graphics:
                    graphics[animName] = []

                graphics[animName].append(
                    parseWindowsBMP(dir + filename, HLSB))
            else:
                graphics[name] = parseWindowsBMP(dir + filename, HLSB)

    return graphics
