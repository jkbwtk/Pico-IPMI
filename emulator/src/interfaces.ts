import { SysInfo } from '#shared/interfaces';


export interface Config {
  mqtt: {
    ip: string;
    login: string;
    password: string;
  }
  hosts: SysInfo[];
}

export interface MQTTSettings {
  ip: string;
  login: string;
  password: string;
}
