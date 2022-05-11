import threading


class Timer(threading.Thread):
    PERIODIC = 0

    def __init__(self, n):
        threading.Thread.__init__(self)
        self.daemon = False
        self.loop = threading.Event()
        self.interval = 0
        self.callback = None
        self.mode = self.PERIODIC

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
            self.callback(self)
