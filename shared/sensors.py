from shared.utils import loadJSON

aliases = loadJSON('./shared/sensorAliases.json')


def parseSensors(data: list, sysInfo: dict):
    l = list(data[2:])

    d = {n: l.pop(0) for n in sorted(aliases.keys()) if not n.startswith('_')}

    cpuUsage = {}
    drives = {}
    smart = {}
    network = {}
    gpu = {}

    for _ in range(sysInfo['cpuThreads']):
        cpuUsage[f'cpu{len(cpuUsage):02}_usage'] = l.pop(0)

    for _ in range(len(sysInfo['drives'])):
        drives[f'drive{len(drives) // 2}_read'] = l.pop(0)
        drives[f'drive{len(drives) // 2}_write'] = l.pop(0)

    for _ in range(len(sysInfo['drives'])):
        smart[f'smart{len(smart) // 6}_temp'] = l.pop(0)
        smart[f'smart{len(smart) // 6}_life'] = l.pop(0)
        smart[f'smart{len(smart) // 6}_warning'] = l.pop(0)
        smart[f'smart{len(smart) // 6}_failure'] = l.pop(0)
        smart[f'smart{len(smart) // 6}_reads'] = l.pop(0)
        smart[f'smart{len(smart) // 6}_writes'] = l.pop(0)

    for _ in range(len(sysInfo['networkInterfaces'])):
        network[f'net{len(network) // 2}_up'] = l.pop(0)
        network[f'net{len(network) // 2}_dl'] = l.pop(0)

    for _ in range(len(sysInfo['gpus'])):
        gpu[f'gpu{len(gpu) // 3}_usage'] = l.pop(0)
        gpu[f'gpu{len(gpu) // 3}_mem_used'] = l.pop(0)
        gpu[f'gpu{len(gpu) // 3}_temp'] = l.pop(0)

    d.update(cpuUsage)
    d.update(drives)
    d.update(smart)
    d.update(network)
    d.update(gpu)

    return d