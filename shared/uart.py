import random
import string
import time
from shared.opcodes import PACKET_STOP


try:
    from machine import Timer
except:
    import threading
    import signal

    TERMINATED = False

    def terminator(signum, frame):
        global TERMINATED

        print('Terminating')
        TERMINATED = True
        raise InterruptedError()

    signal.signal(signal.SIGTERM, terminator)
    signal.signal(signal.SIGINT, terminator)

    class Timer(threading.Thread):
        PERIODIC = 0

        def __init__(self):
            threading.Thread.__init__(self)
            self.daemon = False
            self.loop = threading.Event()

        def init(self, freq, mode, callback):
            self.interval = 1 / freq
            self.mode = mode
            self.callback = callback

            self.start()

        def deinit(self):
            self.loop.set()
            self.join()

        def run(self):
            while not self.loop.wait(self.interval):
                if TERMINATED:
                    return self.deinit()

                self.callback(self)


class UART:
    def __init__(self, uart) -> None:
        self.uart = uart

        self.packetTimer = Timer()
        self.packetTimer.init(freq=1 / 2, mode=Timer.PERIODIC, callback=self.packetChecker)

        self.pendingPackets = {} # noun: [timestamp, retries, packet]

    def __del__(self):
        self.packetTimer.deinit()

    def packetChecker(self, timer):
        now = time.time_ns()
        items = list(self.pendingPackets.items())

        for noun, packet in items:
            if now >= packet[0] + 1_000_000_000:
                if packet[1] >= 5:
                    print('CONNECTION ERROR!', noun, packet)
                    self.pendingPackets.pop(noun)
                    continue

                packet[1] += 1
                packet[0] = now
                print(noun, 'Retries:', packet[1])
                # self.uart.write(packet[2])

    def watchPacket(self, packet: bytes):
        noun = ''.join(random.choice(string.ascii_letters) for _ in range(12))

        self.pendingPackets[noun] = [time.time_ns(), 0, packet]

    def write(self, packet: bytes, important=False):
        if important:
            self.watchPacket(packet)

        self.uart.write(packet)

    def readLine(self):
        firstLoop = True
        buffer = b''

        while True:
            packet: bytes | None = self.uart.read(1)
            if packet == None:
                if firstLoop:
                    return False

                firstLoop = False
                continue

            buffer += packet
            if not buffer.endswith(PACKET_STOP):
                continue

            return buffer
