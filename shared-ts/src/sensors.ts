import { Sensors, SysInfo } from './interfaces';
import { range } from './utils';


export const parseSensors = (sysInfo: SysInfo, data: number[]): Sensors => {
  return {
    batt_charge: data.shift() ?? -1,
    batt_level: data.shift() ?? -1,
    batt_time: data.shift() ?? -1,
    bclk: data.shift() ?? -1,
    cpu_fan: data.shift() ?? -1,
    cpu_power: data.shift() ?? -1,
    cpu_temp: data.shift() ?? -1,
    cpu_usage: data.shift() ?? -1,
    ram_freq: data.shift() ?? -1,
    ram_used: data.shift() ?? -1,
    cpus: range(sysInfo.cpuThreads).map(() => data.shift() ?? -1),
    drives: sysInfo.drives.map(() => ({
      read: data.shift() ?? -1,
      write: data.shift() ?? -1,
    })),
    smart: sysInfo.drives.map(() => ({
      temp: data.shift() ?? -1,
      life: data.shift() ?? -1,
      warning: data.shift() ?? -1,
      failure: data.shift() ?? -1,
      reads: data.shift() ?? -1,
      writes: data.shift() ?? -1,
    })),
    networkInterfaces: sysInfo.networkInterfaces.map(() => ({
      up: data.shift() ?? -1,
      dl: data.shift() ?? -1,
    })),
    gpus: sysInfo.gpus.map(() => ({
      usage: data.shift() ?? -1,
      mem_used: data.shift() ?? -1,
      temp: data.shift() ?? -1,
    })),
  };
};
