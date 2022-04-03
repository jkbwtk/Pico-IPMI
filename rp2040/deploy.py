from sys import argv
import bmpParser
import os
import mpy_cross
import subprocess
import re as regex

COM_PORT = 'COM3'

ignoredFiles = [
    'deploy.py',
    'main.py',
]


if len(argv) == 1 or not argv[1] == 'run':
    # create 'out' directory
    os.makedirs('out', exist_ok=True)

    # clear 'out' directory
    for file in os.listdir('out'):
        os.remove('out/' + file)

    # convert graphics to JSON
    bmpParser.convertToJson('out/graphics.json', 'graphics/')

    # compile modules to '.mpy'
    for file in os.listdir('.'):
        if file.endswith('.py') and file not in ignoredFiles:
            mpy_cross.run('-O2', '-o', 'out/' + file[:-3] + '.mpy', file)

    # clear all files on device
    matcher = regex.compile(r'(\d+) ([^\s]+)')

    remote = subprocess.run(['mpremote',  'ls'], stdout=subprocess.PIPE)
    out = remote.stdout.decode('utf-8').split('\r\n')

    for f in out:
        match = matcher.search(f)

        if match and not match.group(2) == 'lib/':
            if not match.group(2).endswith('/'):
                subprocess.run(
                    ['mpremote', 'connect', COM_PORT, 'rm', match.group(2)])

    # copy new files to device
    for file in os.listdir('out'):
        subprocess.run(['mpremote', 'connect', COM_PORT,
                       'cp', 'out/' + file, ':'])


# run 'main.py'
try:
    subprocess.run(['mpremote', 'connect', COM_PORT,
                   'run', 'main.py'], shell=True)
except KeyboardInterrupt:
    print('Stopping...')
    exit()
