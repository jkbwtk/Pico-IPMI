from shared.utils import time_ns
import time


class Debouncer:
    groups = {}

    def __init__(self, callback, timeout: int, group=None):
        self.last = time.ticks_ms()
        self.callback = callback
        self.timeout = timeout
        self.group = group

    def exec(self, port):
        if self.group is not None:
            if time_ns() > Debouncer.groups.get(self.group, 0) + 50_000_000:
                Debouncer.groups[self.group] = time_ns()
            else:
                return

        if time.ticks_ms() > self.last + self.timeout:
            self.last = time.ticks_ms()
            self.callback(port)


def debounce(timeout: int = 200, group=None):
    if group is not None and group not in Debouncer.groups:
        Debouncer.groups[group] = time_ns()

    def inner(func):
        return Debouncer(func, timeout, group)

    return inner
