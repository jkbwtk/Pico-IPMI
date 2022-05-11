
import platform
import re
import time

import cpuinfo
import GPUtil
import psutil
from shared.utils import loadJSON, parseType

system = platform.system()
aliases = loadJSON('./shared/sensorAliases.json')


# do Gates specific things
if system == 'Windows':
    import winreg

    reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    key = winreg.OpenKey(reg, 'SOFTWARE\\HWiNFO64\\VSB')


def getDrives():
    if system == 'Windows':
        d = readReg()
        r = re.compile(r'^Drive: (.+)$', re.MULTILINE)

        return [
            {
                'name': sensor,
            } for sensor in r.findall('\n'.join(d.keys()))
        ]
    elif system == 'Linux':
        raise NotImplementedError()


def getNetworkInterfaces():
    if system == 'Windows':
        d = readReg()
        r = re.compile(r'^Network: (.+)$', re.MULTILINE)

        return [
            {
                'name': sensor,
            } for sensor in r.findall('\n'.join(d.keys()))
        ]
    elif system == 'Linux':
        raise NotImplementedError()


def getSysInfo() -> dict:
    uname = platform.uname()

    trace = cpuinfo.Trace(True, True)
    cpuid = cpuinfo.CPUID(trace)
    max_extension_support = cpuid.get_max_extension_support()
    brand = cpuid.get_processor_brand(max_extension_support)

    memory = psutil.virtual_memory()
    gpu = GPUtil.getGPUs()

    return {
        # system
        'name': uname.node,
        'os': '{} {}'.format(uname.system, uname.release),
        'arch': uname.machine,
        # 'boot_time': psutil.boot_time() // 1

        # CPU
        'cpuName': brand,
        'cpuCores': psutil.cpu_count(logical=False),
        'cpuThreads': psutil.cpu_count(logical=True),

        # RAM
        'ramTotal': memory.total // 1_048_576,

        # drives
        'drives': getDrives(),

        # network
        'networkInterfaces': getNetworkInterfaces(),

        # GPU
        'gpus': [{
            'name': g.name,
            'vram': g.memoryTotal
        } for g in gpu]
    }


def flatten(s: dict) -> dict:
    fs = {}

    for _, v in s.items():
        fs.update(v)

    return fs


def getFromAlias(v: dict, a: str):
    for aa in aliases[a]:
        vv = v.get(aa, -1)

        if vv != -1:
            return parseType(vv)

    return -1


def mapReg(s: dict):
    fs = flatten(s)

    cpuUsageMatcher = re.compile(r'^Core \d+.+Usage$')
    driveMatcher = re.compile(r'^Drive: .+$')
    smartMatcher = re.compile(r'^S\.M\.A\.R\.T\.: .+$')
    networkMatcher = re.compile(r'^Network: .+$')

    cpuUsage = {}

    for k, v in fs.items():
        if cpuUsageMatcher.match(k):
            cpuUsage[f'cpu{len(cpuUsage):02}_usage'] = parseType(v)

    drives = {}
    smart = {}
    network = {}

    for k, v in s.items():
        if driveMatcher.match(k):
            drives[f'drive{len(drives) // 2}_read'] = getFromAlias(v,
                                                                   '_drive_read')
            drives[f'drive{len(drives) // 2}_write'] = getFromAlias(v,
                                                                    '_drive_write')
        elif smartMatcher.match(k):
            smart[f'smart{len(smart) // 6}_temp'] = getFromAlias(v,
                                                                 '_smart_temp')
            smart[f'smart{len(smart) // 6}_life'] = getFromAlias(v,
                                                                 '_smart_life')
            smart[f'smart{len(smart) // 6}_warning'] = getFromAlias(v,
                                                                    '_smart_warning')
            smart[f'smart{len(smart) // 6}_failure'] = getFromAlias(v,
                                                                    '_smart_failure')
            smart[f'smart{len(smart) // 6}_reads'] = getFromAlias(v,
                                                                  '_smart_reads')
            smart[f'smart{len(smart) // 6}_writes'] = getFromAlias(v,
                                                                   '_smart_writes')
        elif networkMatcher.match(k):
            network[f'net{len(network) // 2}_up'] = getFromAlias(v, '_net_up')
            network[f'net{len(network) // 2}_dl'] = getFromAlias(v, '_net_dl')

    gpu = {}

    for g in GPUtil.getGPUs():
        gpu[f'gpu{len(gpu) // 3}_usage'] = g.load * 100
        gpu[f'gpu{len(gpu) // 3}_mem_used'] = g.memoryUsed
        gpu[f'gpu{len(gpu) // 3}_temp'] = g.temperature

    l = {k: getFromAlias(fs, k) for k in sorted(aliases) if not k.startswith('_')}

    l.update(cpuUsage)
    l.update(drives)
    l.update(smart)
    l.update(network)
    l.update(gpu)

    return l


def readReg():
    r = {}

    for n in range(1024):
        try:
            _, sensor, _ = winreg.EnumValue(key, (n * 5) + 0)
            _, label, _ = winreg.EnumValue(key, (n * 5) + 1)
            _, value, _ = winreg.EnumValue(key, (n * 5) + 3)

            if not sensor in r:
                r[sensor] = dict()

            r[sensor][label] = value

        except:
            break

    return r


def getSensors() -> dict:
    if system == 'Windows':
        return mapReg(readReg())
    elif system == 'Linux':
        # look wherever Torvalds keeps his sensors
        raise NotImplementedError()
    else:
        raise NotImplementedError()
