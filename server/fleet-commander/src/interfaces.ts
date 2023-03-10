import { SysInfo } from '#shared/interfaces';


export interface ModuleData {
  name: string;
  lastPing: number;
  sysInfo: SysInfo | null;
}

export interface Request {
  uniq: number;
  timestamp: number;
  retries: number;
  packet: Buffer;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  resolve: (value: any | PromiseLike<any>) => void;
  reject: (reason?: Error) => void;
}

export interface Config {
  mqtt: {
    ip: string;
    login: string;
    password: string;
    requestRetries: number;
    requestTimeout: number;
  };
  api: {
    port: number;
  };
}
