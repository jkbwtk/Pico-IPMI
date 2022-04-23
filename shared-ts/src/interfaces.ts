export interface SysInfo {
   arch: string;
   cpuCores: number;
   cpuName: string;
   cpuThreads: number;
   drives: {
     name: string;
   }[];
   gpus: {
     name: string;
     vram: number;
   }[];
   name: string;
   networkInterfaces: {
     name: string;

   }[];
   os: string;
   ramTotal: number;
}

export interface SensorAliases {
  [key: string]: string[];
}

export interface Sensors {
  batt_charge: number;
  batt_level: number;
  batt_time: number;
  bclk: number;
  cpu_fan: number;
  cpu_power: number;
  cpu_temp: number;
  cpu_usage: number;
  ram_freq: number;
  ram_used: number;
  cpus: number[];
  drives: {
    read: number;
    write: number;
  }[];
  smart: {
    usage: number;
    life: number;
    warning: number;
    failure: number;
    reads: number;
    writes: number;
  }[];
  networkInterfaces: {
    up: number;
    dl: number;
  }[];
  gpus: {
    usage: number;
    mem_used: number;
    temp: number;
  }[];
}
