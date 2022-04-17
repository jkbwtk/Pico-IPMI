export interface Host {
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

export interface Config {
  mqtt: {
    ip: string;
    login: string;
    password: string;
  }
  hosts: Host[];
}

export interface SensorAliases {
  [key: string]: string[];
}

export interface Sensors {
  [key: string]: number;
}

export interface MQTTSettings {
  ip: string;
  login: string;
  password: string;
}
