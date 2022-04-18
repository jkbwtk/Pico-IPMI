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
  [key: string]: number;
}
