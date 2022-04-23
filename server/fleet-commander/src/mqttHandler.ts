import { connect } from 'mqtt';
import { createRequest, packDataAuto, unpackData } from '#shared/packets';
import { GET_SENSORS, GET_SYSINFO, Opcodes, PING, PONG, REGISTERED, SENSOR_DATA, SYSINFO_DATA } from '#shared/opcodes';
import { Sensors, SysInfo } from '#shared/interfaces';
import { getNonce } from '#shared/utils';
import Deferred from '#shared/Deferred';
import { parseSensors } from '#shared/sensors';
import { ModuleData, Request } from './interfaces';
import config from './config';
import { extractModuleName, picoIn, picoOut, PUBLIC_IN, PUBLIC_OUT } from '#shared/mqttUtils';

type OpcodeHandler = (topic: string, data: unknown[]) => void;


const modules = new Map<string, ModuleData>();
const requests = new Map<string, Request>();

const client = connect(`mqtt://${config.mqtt.ip}`, {
  clientId: 'commander',
  username: config.mqtt.login,
  password: config.mqtt.password,
});


const handleMessage = (topic: string, message: Buffer): void => {
  const [opcode, , ...data] = unpackData(message);
  console.log(topic, '=>', Opcodes[opcode] ?? `INVALID_OPCODE[${opcode}]`, data);

  switch (opcode) {
    case PONG:
      handlePong(topic, data);
      break;

    case SYSINFO_DATA:
      handleSysInfoData(topic, data);
      break;

    case SENSOR_DATA:
      handleSensorData(topic, data);
      break;
  }
};

const handlePong: OpcodeHandler = (topic: string, data: unknown[]) => {
  if (data[0] === undefined || typeof data[0] !== 'string') return;

  if (modules.has(data[0])) {
    client.publish(picoIn(data[0]), createRequest(REGISTERED));
    return;
  }

  modules.set(data[0], { name: data[0], sysInfo: JSON.parse(data[1] as string) });
  client.subscribe(picoOut(data[0]));
  client.publish(picoIn(data[0]), createRequest(REGISTERED));

  console.log(`Added ${data[0]} to tracked modules`);
};

const handleSysInfoData: OpcodeHandler = (topic: string, data: unknown[]) => {
  if (data[0] === undefined || typeof data[0] !== 'string') throw new Error('Invalid data format');
  const nonce = data.shift() as string;

  const request = requests.get(nonce);
  if (request === undefined) return;

  try {
    const sysInfo: SysInfo = JSON.parse(data[0]);

    request.resolve(sysInfo);
    requests.delete(nonce);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(nonce);
    } else {
      request.reject(new Error('JSON parsing failed'));
      requests.delete(nonce);
    }
  }
};

const handleSensorData = (topic: string, data: unknown[]) => {
  if (data[0] === undefined || typeof data[0] !== 'string') throw new Error('Invalid data format');
  const nonce = data.shift() as string;

  const module = modules.get(extractModuleName(topic));
  if (module === undefined) throw new Error('Module not registered');

  const request = requests.get(nonce);
  if (request === undefined) return;


  try {
    const sensors: Sensors = parseSensors(module.sysInfo, data as number[]);

    request.resolve(sensors);
    requests.delete(nonce);
  } catch (err) {
    if (err instanceof Error) {
      request.reject(err);
      requests.delete(nonce);
    } else {
      request.reject(new Error('Sensor parsing failed'));
      requests.delete(nonce);
    }
  }
};

const makeRequest = async <T>(opcode: Opcodes, targetRAW?: string) => {
  let target = PUBLIC_IN;
  if (targetRAW !== undefined) {
    if (!modules.has(targetRAW)) throw new Error('MODULE NOT FOUND');
    target = picoIn(targetRAW);
  }

  const nonce = getNonce();

  return await sendRequest<T>(target, nonce, packDataAuto(opcode, nonce)).promise;
};

const sendRequest = <T>(topic: string, nonce: string, packet: Buffer): Deferred<T> => {
  const hook = new Deferred<T>();


  requests.set(nonce, {
    nonce,
    timestamp: Date.now(),
    retries: 0,
    packet,
    resolve: hook.resolve,
    reject: hook.reject,
  });

  setTimeout(() => {
    if (requests.has(nonce)) {
      console.log('Request failed, running cleanup');
      requests.delete(nonce);
      hook.reject(new Error('Request timed out'));
    }
  }, 5 * 1000);

  client.publish(topic, packet);

  return hook;
};

const sendPing = (): void => {
  client.publish(PUBLIC_IN, createRequest(PING));
};


export const getSysInfo = async (target?: string): Promise<{ name: string; data: SysInfo; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_SYSINFO, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<SysInfo>(GET_SYSINFO, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const getSensors = async (target?: string): Promise<{ name: string; data: Sensors; }[]> => {
  if (target !== undefined) return [{ name: target, data: await makeRequest(GET_SENSORS, target) }];

  const names = Array.from(modules.keys());
  const d = await Promise.all(names.map((name) => makeRequest<Sensors>(GET_SENSORS, name)));

  return names.map((name, index) => ({ name, data: d[index] }));
};

export const getModule = (target?: string): {name: string, data: ModuleData}[] => {
  if (target !== undefined) {
    const module = modules.get(target);
    if (module === undefined) throw new Error('MODULE NOT FOUND');

    return [{ name: target, data: module }];
  }

  return Array.from(modules.entries()).map(([name, data]) => ({ name, data }));
};


client.subscribe(PUBLIC_OUT);

client.on('message', handleMessage);
client.on('connect', sendPing);
client.on('reconnect', sendPing);

client.on('error', console.log);
