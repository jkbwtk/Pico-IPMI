from sys import argv
import time
import bmpParser
import os
import mpy_cross
import subprocess
import re as regex
import shutil


ignoredFiles = [
    'deploy.py',
    'main.py',
]


switches = {
    'COMPILE': False,
    'RUN': False,
    'COM': 'COM3',
    'OLVL': 3,
}


def parseArgs():
    global switches

    if '-c' in argv:
        switches['COMPILE'] = True

    if '-run' in argv:
        switches['RUN'] = True

    matchOLevel = regex.compile(r'-O(\d)')
    matchCOM = regex.compile(r'-COM=([^\s]+)')

    for arg in argv:
        if matchOLevel.match(arg):
            switches['OLVL'] = matchOLevel.match(arg).group(1)

        if matchCOM.match(arg):
            switches['COM'] = matchCOM.match(arg).group(1)

    print(switches)


def prepOutDir():
    # create 'out' directory
    os.makedirs('out', exist_ok=True)

    # clear 'out' directory
    for file in os.listdir('out'):
        os.remove('out/' + file)


def compileModules():
    global ignoredFiles, switches

    # compile modules to '.mpy'
    for file in os.listdir('.'):
        if file.endswith('.py') and file not in ignoredFiles:
            mpy_cross.run('-O' + switches['OLVL'],
                          '-o', 'out/' + file[:-3] + '.mpy', file)


def copyModules():
    # copy '.py' files to 'out' dir
    for file in os.listdir('.'):
        if file.endswith('.py') and file not in ignoredFiles:
            shutil.copy(file, 'out/')


def convertGraphics():
    # convert graphics to JSON
    bmpParser.convertToJson('out/graphics.json', 'graphics/')


def clearFilesOnDevice():
    global switches
    # clear all files on device
    matcher = regex.compile(r'(\d+) ([^\s]+)')

    remote = subprocess.run(
        ['mpremote', 'connect', switches['COM'], 'ls'], stdout=subprocess.PIPE)
    out = remote.stdout.decode('utf-8').split('\r\n')

    for f in out:
        match = matcher.search(f)

        if match and not match.group(2) == 'lib/':
            if not match.group(2).endswith('/'):
                subprocess.run(
                    ['mpremote', 'connect', switches['COM'], 'rm', match.group(2)])


def copyFilesToDevice():
    global switches
    # copy new files to device
    for file in os.listdir('out'):
        subprocess.run(['mpremote', 'connect', switches['COM'],
                       'cp', 'out/' + file, ':'])


def armDevice():
    subprocess.run(
        ['mpremote', 'connect', switches['COM'], 'cp', 'main.py', ':'])
    time.sleep(2)
    subprocess.run(['mpremote', 'connect', switches['COM'], 'reset'])


parseArgs()

if switches['RUN']:
    try:
        subprocess.run(['mpremote', 'connect', switches['COM'],
                        'run', 'main.py'], shell=True)
    except KeyboardInterrupt:
        print('Stopping...')
        exit()
else:
    prepOutDir()
    convertGraphics()

    if switches['COMPILE']:
        compileModules()
    else:
        copyModules()

    clearFilesOnDevice()
    copyFilesToDevice()
    armDevice()
