import { connect } from 'mqtt';
import { packData, unpackData } from '#shared/packets';
import {
  AMBIENT_TEMP_DATA,
  COMM_POWER,
  COMM_RESET,
  COMM_SLEEP,
  ERR_UNSUPPORTED_OPCODE,
  GET_AMBIENT_TEMP,
  GET_HDD_ACTIVITY,
  GET_POWER_STATUS,
  GET_SENSORS,
  GET_SYSINFO,
  GET_WIFI,
  HDD_ACTIVITY_DATA,
  OK,
  Opcodes,
  PING,
  PONG,
  POWER_STATUS_DATA,
  REGISTER,
  REGISTERED,
  REGISTRATION_DATA,
  SENSOR_DATA,
  SYSINFO_DATA,
  WIFI_DATA,
} from '#shared/opcodes';
import { Packet, Sensors, SysInfo } from '#shared/interfaces';
import { getUniq } from '#shared/utils';
import Deferred from '#shared/Deferred';
import { parseSensors } from '#shared/sensors';
import { ModuleData, Request } from './interfaces';
import config from './config';
import { extractModuleName, picoIn, picoOut, PUBLIC_IN, PUBLIC_OUT } from '#shared/mqttUtils';
import { COMM, ESP, HOST, PICO, PRIVATE, PUBLIC, Routes } from '#shared/routes';
import { ModuleNotFound, RequestTimeout, UnsuportedOpcode } from './errors';

type OpcodeHandler = (topic: string, packet: Packet) => void;


const modules = new Map<string, ModuleData>();
const requests = new Map<number, Request>();

const client = connect(`mqtt://${config.mqtt.ip}`, {
  clientId: 'commander',
  username: config.mqtt.login,
  password: config.mqtt.password,
});


const conectivityCheckLoop = (): void => {
  for (const [module, data] of modules.entries()) {
    if (data.sysInfo === null) {
      writePacket(packData(REGISTER, COMM, ESP, getUniq(), PRIVATE), module);
      continue;
    }

    if (data.lastPing + 15_000 < Date.now()) {
      console.log(`Connection with ${module} lost`);
      writePacket(packData(REGISTER, COMM, ESP, getUniq(), PRIVATE), module);
      modules.delete(module);
    }
  }
};


const handleMessage = (topic: string, message: Buffer): void => {
  let p: Packet | undefined;

  try {
    const packet = unpackData(message);
    p = packet;
    console.log(topic, '=>',
      Opcodes[packet.opcode as number] ?? `INVALID_OPCODE[${packet.opcode}]`,
      Routes[packet.origin as number] ?? `INVALID_SOURCE[${packet.origin}]`,
      Routes[packet.destination as number] ?? `INVALID_DESTINATION[${packet.destination}]`,
      packet.uniq,
      packet.data,
    );

    switch (packet.opcode) {
      case PING:
        handlePing(topic, packet);
        break;

      case PONG:
        handlePong(topic, packet);
        break;

      case REGISTRATION_DATA:
        handleRegistrationData(topic, packet);
        break;

      case SYSINFO_DATA:
        handleSysInfoData(topic, packet);
        break;

      case SENSOR_DATA:
        handleSensorData(topic, packet);
        break;

      case WIFI_DATA:
        handleWiFiData(topic, packet);
        break;

      case POWER_STATUS_DATA:
        handlePowerStatusData(topic, packet);
        break;

      case HDD_ACTIVITY_DATA:
        handleHDDActivityData(topic, packet);
        break;

      case AMBIENT_TEMP_DATA:
        handleAmbientTempData(topic, packet);
        break;

      case OK:
        handleOk(topic, packet);
        break;

      case ERR_UNSUPPORTED_OPCODE:
        handleErrUnsupportedOpcode(topic, packet);
        break;

      default:
        client.publish(picoIn(extractModuleName(topic)), packData(ERR_UNSUPPORTED_OPCODE, packet.destination, packet.origin, packet.uniq, packet.channel));
        break;
    }
  } catch (err) {
    console.log(topic, '=>', p, 'ERROR', err);
  }
};


const handlePing: OpcodeHandler = (topic: string, packet: Packet) => {
  if (packet.channel !== PRIVATE && packet.origin !== ESP) {
    return writePacket(packData(PONG, packet.destination, packet.origin, packet.uniq, PRIVATE), extractModuleName(topic));
  }

  const module = modules.get(extractModuleName(topic));

  if (module === undefined) {
    console.log(`Module ${extractModuleName(topic)} not registered, attempting to register`);
    return writePacket(packData(REGISTER, COMM, ESP, packet.uniq, PUBLIC));
  }

  module.lastPing = Date.now();
  return writePacket(packData(PONG, COMM, ESP, packet.uniq, PRIVATE), extractModuleName(topic));
};

const handlePong: OpcodeHandler = (topic: string, packet: Packet) => {
  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  request.resolve({});
  requests.delete(packet.uniq);
};

const handleRegistrationData: OpcodeHandler = async (topic: string, packet: Packet) => {
  if (packet.data[0] === undefined || typeof packet.data[0] !== 'string') throw new Error('Invalid packet, no module name provided');
  if (packet.data[1] === undefined || typeof packet.data[1] !== 'string') throw new Error('Invalid packet, no sysInfo provided');
  const name = packet.data[0];

  if (modules.has(name)) {
    client.publish(picoIn(name), packData(REGISTERED, COMM, ESP, packet.uniq, PRIVATE));
    return;
  }

  try {
    // client.subscribe(picoOut(name));
    const sysInfo: SysInfo = JSON.parse(packet.data[1]);


    modules.set(name, { name, lastPing: Date.now(), sysInfo });
    client.publish(picoIn(name), packData(REGISTERED, COMM, ESP, packet.uniq, PRIVATE));

    console.log(`Added ${name} to tracked modules`);
  } catch (err) {
    if (err instanceof Error) throw err;
    else throw new Error('SysInfo parsing failed');
  }
};

const handleSysInfoData: OpcodeHandler = (topic: string, packet: Packet) => {
  if (packet.data[0] === undefined || typeof packet.data[0] !== 'string') throw new Error('Invalid packet, no sysInfo provided');

  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  try {
    const sysInfo: SysInfo = JSON.parse(packet.data[0]);

    request.resolve(sysInfo);
    requests.delete(packet.uniq);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(packet.uniq);
    } else {
      request.reject(new Error('SysInfo parsing failed'));
      requests.delete(packet.uniq);
    }
  }
};

const handleSensorData = (topic: string, packet: Packet) => {
  const module = modules.get(extractModuleName(topic));
  if (module === undefined) throw new Error('Module not registered');

  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  try {
    if (module.sysInfo === null) throw new Error('Module sysInfo not received');
    const sensors: Sensors = parseSensors(module.sysInfo, packet.data.slice(1) as number[]);

    request.resolve(sensors);
    requests.delete(packet.uniq);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(packet.uniq);
    } else {
      request.reject(new Error('Sensor parsing failed'));
      requests.delete(packet.uniq);
    }
  }
};

const handleWiFiData: OpcodeHandler = (topic: string, packet: Packet) => {
  if (packet.data[0] === undefined || typeof packet.data[0] !== 'number') throw new Error('Invalid packet, no wifi data provided');

  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  try {
    request.resolve(packet.data[0]);
    requests.delete(packet.uniq);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(packet.uniq);
    } else {
      request.reject(new Error('Resolving failed'));
      requests.delete(packet.uniq);
    }
  }
};

const handlePowerStatusData: OpcodeHandler = (topic: string, packet: Packet) => {
  if (packet.data[0] === undefined || typeof packet.data[0] !== 'number') throw new Error('Invalid packet, no power status data provided');

  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  try {
    request.resolve(packet.data[0]);
    requests.delete(packet.uniq);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(packet.uniq);
    } else {
      request.reject(new Error('Resolving failed'));
      requests.delete(packet.uniq);
    }
  }
};

const handleHDDActivityData: OpcodeHandler = (topic: string, packet: Packet) => {
  if (packet.data.length === 0) throw new Error('Invalid packet, no hdd activity data provided');

  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  try {
    request.resolve(packet.data);
    requests.delete(packet.uniq);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(packet.uniq);
    } else {
      request.reject(new Error('Resolving failed'));
      requests.delete(packet.uniq);
    }
  }
};

const handleAmbientTempData: OpcodeHandler = (topic: string, packet: Packet) => {
  if (packet.data[0] === undefined || typeof packet.data[0] !== 'number') throw new Error('Invalid packet, no ambient temp data provided');

  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  try {
    request.resolve(packet.data[0]);
    requests.delete(packet.uniq);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(packet.uniq);
    } else {
      request.reject(new Error('Resolving failed'));
      requests.delete(packet.uniq);
    }
  }
};

const handleOk: OpcodeHandler = (topic: string, packet: Packet) => {
  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  request.resolve({});
  requests.delete(packet.uniq);
};

const handleErrUnsupportedOpcode: OpcodeHandler = (topic: string, packet: Packet) => {
  const request = requests.get(packet.uniq);
  if (request === undefined) return;

  request.reject(new UnsuportedOpcode(packet.opcode));
};

const writePacket = (packet: Buffer, targetRAW?: string) => {
  let target = PUBLIC_IN;
  if (targetRAW !== undefined) {
    if (!modules.has(targetRAW)) throw new ModuleNotFound(targetRAW);
    target = picoIn(targetRAW);
  }

  // const message = packData(packet.opcode, packet.origin, packet.destination, packet.nonce, packet.channel, ...packet.data);

  client.publish(target, packet);
};

const makeRequest = async <T>(opcode: Opcodes, destination: Routes, targetRAW?: string) => {
  let target = PUBLIC_IN;
  if (targetRAW !== undefined) {
    if (!modules.has(targetRAW)) throw new ModuleNotFound(targetRAW);
    target = picoIn(targetRAW);
  }

  const uniq = getUniq();

  return sendRequest<T>(target, uniq, packData(opcode, COMM, destination, uniq, PRIVATE)).promise;
};

const sendRequest = <T>(topic: string, uniq: number, packet: Buffer): Deferred<T> => {
  const hook = new Deferred<T>();


  requests.set(uniq, {
    uniq,
    timestamp: Date.now(),
    retries: 0,
    packet,
    resolve: hook.resolve,
    reject: hook.reject,
  });


  requestTimeout(topic, uniq, packet);
  client.publish(topic, packet);

  return hook;
};

const requestTimeout = (topic: string, uniq: number, packet: Buffer): void => {
  setTimeout(() => {
    const request = requests.get(uniq);
    if (request === undefined) return;

    if (request.retries >= config.mqtt.requestRetries) {
      console.log(`Request [${uniq}] failed, running cleanup`);
      requests.delete(uniq);
      request.reject(new RequestTimeout(uniq));
      return;
    }

    request.retries += 1;
    request.timestamp = Date.now();
    console.log(`Request [${uniq}] timed out, retries [${request.retries}]`);
    requestTimeout(topic, uniq, packet);
    client.publish(topic, packet);
  }, config.mqtt.requestTimeout);
};

const sendRegister = (): void => {
  client.publish(PUBLIC_IN, packData(REGISTER, COMM, ESP, getUniq(), PUBLIC));
};


export const getSysInfo = async (target?: string): Promise<{ name: string; data: SysInfo; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_SYSINFO, PICO, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<SysInfo>(GET_SYSINFO, PICO, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const getSensors = async (target?: string): Promise<{ name: string; data: Sensors; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_SENSORS, HOST, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<Sensors>(GET_SENSORS, HOST, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const getModule = (target?: string): {name: string, data: ModuleData}[] => {
  if (target !== undefined) {
    const module = modules.get(target);
    if (module === undefined) throw new ModuleNotFound(target);

    return [{ name: target, data: module }];
  }

  return Array.from(modules.entries()).map(([name, data]) => ({ name, data }));
};

export const getWiFi = async (target?: string): Promise<{ name: string; data: number; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_WIFI, ESP, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<number>(GET_WIFI, ESP, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const getPowerStatus = async (target?: string): Promise<{ name: string; data: number; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_POWER_STATUS, PICO, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<number>(GET_POWER_STATUS, PICO, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const getHDDActivity = async (target?: string): Promise<{ name: string; data: number[]; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_HDD_ACTIVITY, PICO, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<number[]>(GET_HDD_ACTIVITY, PICO, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const getAmbientTemp = async (target?: string): Promise<{ name: string; data: number; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_AMBIENT_TEMP, PICO, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<number>(GET_AMBIENT_TEMP, PICO, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const postPower = async (target: string): Promise<void> => {
  await makeRequest(COMM_POWER, PICO, target);
};

export const postReset = async (target: string): Promise<void> => {
  await makeRequest(COMM_RESET, PICO, target);
};

export const postSleep = async (target: string): Promise<void> => {
  await makeRequest(COMM_SLEEP, PICO, target);
};

client.subscribe(PUBLIC_OUT);
client.subscribe(picoOut('+'));

client.on('message', handleMessage);
client.on('connect', sendRegister);
client.on('reconnect', sendRegister);

client.on('error', console.log);

const conectivityChecker = setInterval(conectivityCheckLoop, 100);
