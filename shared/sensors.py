def parseSensors(data: list, sysInfo: dict):
    return {
        'batt_charge': data.pop(0),
        'batt_level': data.pop(0),
        'batt_time': data.pop(0),
        'bclk': data.pop(0),
        'cpu_fan': data.pop(0),
        'cpu_power': data.pop(0),
        'cpu_temp': data.pop(0),
        'cpu_usage': data.pop(0),
        'ram_freq': data.pop(0),
        'ram_used': data.pop(0),
        'cpus': [data.pop(0) for _ in range(sysInfo['cpuThreads'])],
        'drives': [{
            'read': data.pop(0),
            'write': data.pop(0)
        } for _ in range(len(sysInfo['drives']))],
        'smart': [{
            'temp': data.pop(0),
            'life': data.pop(0),
            'warning': data.pop(0),
            'failure': data.pop(0),
            'reads': data.pop(0),
            'writes': data.pop(0)
        } for _ in range(len(sysInfo['drives']))],
        'networkInterfaces': [{
            'up': data.pop(0),
            'dl': data.pop(0)
        } for _ in range(len(sysInfo['networkInterfaces']))],
        'gpus': [{
            'usage': data.pop(0),
            'mem_used': data.pop(0),
            'temp': data.pop(0)
        } for _ in range(len(sysInfo['gpus']))]
    }
