import { Host, SensorAliases, Sensors } from './interfaces';
import { join } from 'path';
import { loadJSON, padLeft } from './utils';

export const aliases: SensorAliases = loadJSON(join(__dirname, '..', '..', 'shared', 'sensorAliases.json'));


export const parseSensors = (data: number[], sysInfo: Host): Sensors => {
  const l = data.slice(2);

  const d: Sensors = {};

  for (const k of Object.keys(aliases).sort()) {
    if (k.startsWith('_')) continue;

    d[k] = l.shift() ?? -1;
  }


  for (let i = 0; i < sysInfo.cpuThreads; i += 1) {
    d[`cpu${padLeft(i, 2, '0')}_usage`] = l.shift() ?? -1;
  }

  for (let i = 0; i < sysInfo.drives.length; i += 1) {
    d[`drive${i}_read`] = l.shift() ?? -1;
    d[`drive${i}_write`] = l.shift() ?? -1;
  }

  for (let i = 0; i < sysInfo.drives.length; i += 1) {
    d[`smart${i}_usage`] = l.shift() ?? -1;
    d[`smart${i}_life`] = l.shift() ?? -1;
    d[`smart${i}_warning`] = l.shift() ?? -1;
    d[`smart${i}_failure`] = l.shift() ?? -1;
    d[`smart${i}_reads`] = l.shift() ?? -1;
    d[`smart${i}_writes`] = l.shift() ?? -1;
  }

  for (let i = 0; i < sysInfo.networkInterfaces.length; i += 1) {
    d[`net${i}_up`] = l.shift() ?? -1;
    d[`net${i}_dl`] = l.shift() ?? -1;
  }

  for (let i = 0; i < sysInfo.gpus.length; i += 1) {
    d[`gpu${i}_usage`] = l.shift() ?? -1;
    d[`gpu${i}_mem_used`] = l.shift() ?? -1;
    d[`gpu${i}_temp`] = l.shift() ?? -1;
  }


  return d;
};
