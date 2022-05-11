PUBLIC_OUT = 'public/out'
PUBLIC_IN = 'public/in'


def picoOut(module: bytes) -> str:
    return f"pico/{module.decode('utf-8')}/out"


def picoIn(module: bytes) -> str:
    return f"pico/{module.decode('utf-8')}/in"


def reverseTopic(topic: str) -> str:
    if topic == PUBLIC_OUT:
        return PUBLIC_IN
    elif topic == PUBLIC_IN:
        return PUBLIC_OUT

    [_, module, direction] = topic.split('/')
    return picoIn(module) if direction == 'out' else picoOut(module)


def extractModuleName(topic: str) -> str:
    [channel, module] = topic.split('/')

    if channel == 'public':
        return ''
    else:
        return module
