import { connect, MqttClient } from 'mqtt';
import { clamp, clampCeil, flatten, getUniq, hash, hashInt, range, timeNow } from '#shared/utils';
import { packData, unpackData } from '#shared/packets';
import {
  AMBIENT_TEMP_DATA,
  COMM_POWER,
  COMM_RESET,
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
  TEST_DATA,
  WIFI_DATA,
} from '#shared/opcodes';
import { Packet, Sensors, SysInfo } from '#shared/interfaces';
import { MQTTSettings } from 'interfaces';
import { picoIn, picoOut, PUBLIC_IN, PUBLIC_OUT } from '#shared/mqttUtils';
import { COMM, ESP, PICO, PRIVATE, PUBLIC, Routes } from '#shared/routes';


export default class Module {
  mqtt_id: string;
  name: string;
  host: SysInfo;
  mqttSettings: MQTTSettings;
  client: MqttClient;
  connected = false;
  state: { power: boolean; hddactivity: boolean[]; };
  heartbeat: NodeJS.Timer;
  fakeHDDActivity: NodeJS.Timer;

  constructor(host: SysInfo, mqttSettings: MQTTSettings) {
    this.mqtt_id = `emu_${hash(host.name)}`;
    this.name = `${host.name}(${this.mqtt_id})`;

    this.host = host;
    this.mqttSettings = mqttSettings;

    this.state = {
      power: false,
      hddactivity: Array.from({ length: 100 }, () => false),
    };

    this.client = connect(`mqtt://${this.mqttSettings.ip}`, {
      clientId: this.mqtt_id,
      username: this.mqttSettings.login,
      password: this.mqttSettings.password,
    });

    this.client.subscribe(picoIn(this.mqtt_id));
    this.client.subscribe(PUBLIC_IN);

    this.client.on('message', this.handleMessage.bind(this));
    this.client.on('connect', this.registerComm.bind(this));
    this.client.on('reconnect', this.registerComm.bind(this));

    this.client.on('error', this.log.bind(this));

    this.heartbeat = setInterval(() => {
      if (!this.client.connected) return;

      this.routePacket(PING, ESP, COMM, getUniq(), PRIVATE);
    }, 5000);

    this.fakeHDDActivity = setInterval(() => {
      this.state.hddactivity.shift();

      const chances = this.state.hddactivity[99] ? 0.6 : 0.3;
      this.state.hddactivity.push(Math.random() < chances);
    }, 100);
  }

  private log(message: unknown, ...args: unknown[]) {
    console.log(`[${this.name}]`, message, ...args);
  }

  private handleMessage(topic: string, message: Buffer) {
    let p: Packet | undefined;

    try {
      const packet = unpackData(message);
      p = packet;
      this.log(topic, '=>',
        Opcodes[packet.opcode as number] ?? `INVALID_OPCODE[${packet.opcode}]`,
        Routes[packet.origin as number] ?? `INVALID_SOURCE[${packet.origin}]`,
        Routes[packet.destination as number] ?? `INVALID_DESTINATION[${packet.destination}]`,
        packet.uniq,
        Routes[packet.channel as number] ?? `INVALID_CHANNEL[${packet.channel}]`,
        packet.data,
      );

      switch (packet.opcode) {
        case PING:
          this.routePacket(PONG, packet.destination, packet.origin, packet.uniq, packet.channel);
          break;
        case PONG:
          break;

        case COMM_POWER:
          this.state.power = !this.state.power;
          this.routePacket(OK, packet.destination, packet.origin, packet.uniq, packet.channel);
          break;
        case COMM_RESET:
          this.log('Reset');
          this.routePacket(OK, packet.destination, packet.origin, packet.uniq, packet.channel);
          break;

        case GET_SENSORS:
          this.routePacket(SENSOR_DATA, packet.destination, packet.origin, packet.uniq, packet.channel, ...flatten(this.getFakeSensors(timeNow())));
          break;
        case GET_SYSINFO:
          this.routePacket(SYSINFO_DATA, packet.destination, packet.origin, packet.uniq, packet.channel, JSON.stringify(this.host));
          break;
        case GET_WIFI:
          this.routePacket(WIFI_DATA, packet.destination, packet.origin, packet.uniq, packet.channel, this.getFakeSignalPower(timeNow()));
          break;
        case GET_POWER_STATUS:
          this.routePacket(POWER_STATUS_DATA, packet.destination, packet.origin, packet.uniq, packet.channel, this.state.power);
          break;
        case GET_HDD_ACTIVITY:
          this.routePacket(HDD_ACTIVITY_DATA, packet.destination, packet.origin, packet.uniq, packet.channel, ...this.state.hddactivity);
          break;
        case GET_AMBIENT_TEMP:
          this.routePacket(AMBIENT_TEMP_DATA, packet.destination, packet.origin, packet.uniq, packet.channel, this.getFakeAmbientTemp(timeNow()));
          break;

        case REGISTER:
          this.connected = false;
          this.registerComm();
          break;
        case REGISTERED:
          this.log('Registered');
          this.connected = true;
          break;

        default:
          this.routePacket(ERR_UNSUPPORTED_OPCODE, packet.destination, packet.origin, packet.uniq, packet.channel);
          break;
      }
    } catch (err) {
      this.log(topic, '=>', p, 'ERROR', err);
    }
  }

  private routePacket(opcode: Opcodes, origin: Routes, destination: Routes, uniq: number, channel: Routes, ...data: (string | number | boolean)[]) {
    const packet = packData(opcode, destination, origin, uniq, channel, ...data);
    const topic = destination === PUBLIC ? PUBLIC_OUT : picoOut(this.mqtt_id);

    this.client.publish(topic, packet);
  }

  private registerComm() {
    this.routePacket(REGISTRATION_DATA, ESP, COMM, getUniq(), PUBLIC, this.mqtt_id, JSON.stringify(this.host));
  }

  private get systemSpecs() {
    const host = this.host;

    return {
      has_battery: hashInt(host.name + 'battery') % 5 == 0 ? true : false,
      batt_capacity: 35 + hashInt(host.name + 'capacity') % 14 * 5,
      batt_charge_speed: 15 + hashInt(host.name + 'charge') % 22 * 5,
      batt_voltage: 4 + hashInt(host.name + 'voltage') % 9,

      cpu_tdp: 10 + hashInt(host.cpuName + 'pow') % 23 * 5,
      fan_rpm: 500 + hashInt(host.name + host.cpuName + 'fan') % 21 * 100,
      cooler_efficency: 0.6 + hashInt(host.name + host.cpuName + 'eff') % 5 * 0.1,

      bclk_change_rate: 30 + hashInt(host.name + 'bclk_rate') % 121,

      get gpus() {
        const gpus = [];

        for (let i = 0; i < host.gpus.length; i += 1) {
          const gpu = host.gpus[i];

          gpus.push({
            tdp: 50 + hashInt(gpu.name + 'gpu_pow') % 31 * 10,
            cooler_efficency: 0.6 + hashInt(gpu.name + 'gpu_eff') % 5 * 0.1,
          });
        }

        return gpus;
      },

      get drives() {
        const drives = [];

        for (let i = 0; i < host.drives.length; i += 1) {
          const drive = host.drives[i];

          drives.push({
            max_read: 50 + hashInt(drive.name + 'read') % 46 * 10,
            max_write: 50 + hashInt(drive.name + 'write') % 46 * 10,
            has_life: hashInt(drive.name + 'drive_life') % 4 == 0 ? true : false,
            starting_life: Math.floor(100 - (1.0598 ** ((hashInt('life' + drive.name) % 101) - 20))),
            starting_reads: hashInt(drive.name + 'reads'),
            starting_writes: hashInt(drive.name + 'writes'),
          });
        }

        return drives;
      },

      get networkInterfaces() {
        const networkInterfaces = [];

        for (let i = 0; i < host.networkInterfaces.length; i += 1) {
          const networkInterface = host.networkInterfaces[i];

          networkInterfaces.push({
            max_dl: 5 + Math.round(1.02 ** (hashInt(networkInterface.name + 'dl') % 265)) * 5,
            max_up: 5 + Math.round(1.02 ** (hashInt(networkInterface.name + 'up') % 265)) * 5,
          });
        }

        return networkInterfaces;
      },
    };
  }

  private getFakeSensors(offsetRAW = 0): Sensors {
    const scale = 60;
    const offset = offsetRAW + hashInt(this.host.name + this.host.cpuName + this.host.arch);


    // const sensors = this.generateSensors(offset, scale);
    const specs = this.systemSpecs;

    // eslint-disable-next-line max-len
    const batt_level = (o: number) => Math.sin(hashInt(this.host.name) + o * Math.PI / (specs.batt_capacity / (specs.batt_charge_speed / specs.batt_voltage)) / 60 / scale) * 45 + 55;
    const cpu_usage = (v: number) => clamp(0, 100, (1.02 ** (((hashInt(Math.floor(hashInt(this.host.cpuName) + offset / v)) % 5000) / 20) + 150)) / 25);
    // eslint-disable-next-line max-len
    const drive_read = (i: number) => clamp(0, specs.drives[i].max_read, specs.drives[i].max_read * (((hashInt(Math.floor(offset / scale) + (i + 20).toString() + 'drive_read') / 10000) % 1) ** 10) + (((hashInt(offset) / 1000) % 10) - 5));
    // eslint-disable-next-line max-len
    const drive_write = (i: number) => clamp(0, specs.drives[i].max_write, specs.drives[i].max_write * (((hashInt(Math.floor(offset / scale) + (i + 20).toString() + 'drive_write') / 10000) % 1) ** 12) + (((hashInt(offset) / 1000) % 10) - 5));
    // eslint-disable-next-line max-len
    const gpu_usage = (i: number) => clamp(0, 100, (1.02 ** (((hashInt(Math.floor(hashInt(this.host.gpus[i].name) + Math.floor(offset / scale))) % 5000) / 20) + 150)) / 25 + ((hashInt(offset + this.host.cpuName) % 1001) / 100));

    const cpuUsage = clampCeil(100, cpu_usage((cpu_usage(180) * (Math.floor(offset / scale)) % 240)) + ((hashInt(offset + 'cpu') % 1001) / 100));
    const cpuPower = 15 + cpuUsage * specs.cpu_tdp / 100 + (((hashInt(offset / 5 + 'cpu_pow') % 101) / 10) - 5);
    const cpuTemp = clampCeil(105, 25 + 35 * ((cpuPower / specs.cpu_tdp) / specs.cooler_efficency));


    const distCpuLoad = (cpuUsage: number) => {
      let remCpu: number = cpuUsage;
      const cpuLoad = [];

      for (let i = 0; i < this.host.cpuThreads; i += 1) {
        const usage = clampCeil(100, remCpu) * (((hashInt(offset * (i + 20) + 'core') / 10000) % 1) ** 3.5);
        remCpu -= usage / this.host.cpuThreads;

        cpuLoad.push(usage);
      }

      while (remCpu > 0.001) {
        for (let i = 0; i < this.host.cpuThreads; i += 1) {
          const topup = clampCeil(100 - cpuLoad[i], remCpu);
          remCpu -= topup / this.host.cpuThreads;

          cpuLoad[i] += topup;
        }
      }


      return cpuLoad;
    };


    return {
      batt_charge: batt_level(offset) > batt_level(offset - 1) ? specs.batt_charge_speed : 0,
      batt_level: batt_level(offset),
      // eslint-disable-next-line max-len
      batt_time: batt_level(offset) < batt_level(offset - 1) ? 60 * (specs.batt_capacity / 100 * batt_level(offset)) / (specs.batt_charge_speed / specs.batt_voltage) : 0,
      bclk: 100 - Math.max(0, Math.round(1.01 ** (hashInt(hashInt(this.host.name) + Math.floor(offset / specs.bclk_change_rate / 60)) % 650) / 10) / 10 - 0.3),
      cpu_fan: clampCeil(specs.fan_rpm, Math.round(cpuTemp / 95 * specs.fan_rpm)),
      cpu_power: cpuPower,
      cpu_temp: cpuTemp,
      cpu_usage: cpuUsage,
      ram_freq: 1200 + hashInt(this.host.name + 'freq') % 10 * 200,
      // eslint-disable-next-line max-len
      ram_used: clampCeil(Math.ceil(this.host.ramTotal), Math.round(((2048 + (((1.002 ** (((hashInt(hashInt(this.host.cpuName) + Math.floor(offset / 360)) % 1500) + 2000)))) / 1200) * this.host.ramTotal) + (cpuUsage / 100 * this.host.ramTotal)))),
      cpus: distCpuLoad(cpuUsage),
      drives: range(this.host.drives.length).map((i) => ({
        read: drive_read(i),
        write: drive_write(i),
      })),
      smart: range(this.host.drives.length).map((i) => ({
        temp: 25 + (cpuTemp / 15) + (hashInt(offset + this.host.drives[i].name + i.toString()) % 10),
        life: specs.drives[i].has_life ? specs.drives[i].starting_life - Math.floor(offsetRAW / 360 / scale) : -1,
        warning: 0,
        failure: 0,
        reads: specs.drives[i].starting_reads + Math.floor(offsetRAW / 30 / scale),
        writes: specs.drives[i].starting_writes + Math.floor(offsetRAW / 30 / scale),
      })),
      networkInterfaces: range(this.host.networkInterfaces.length).map((i) => ({
        // eslint-disable-next-line max-len
        up: clamp(0, specs.networkInterfaces[i].max_up, specs.networkInterfaces[i].max_up * (((hashInt(Math.floor(offset / (cpuUsage ?? 1 * scale)) + (i + 20).toString() + 'up') / 10000) % 1) ** 10) + (((hashInt(offset) / 1000) % 10) - 5)),
        // eslint-disable-next-line max-len
        dl: clamp(0, specs.networkInterfaces[i].max_dl, specs.networkInterfaces[i].max_dl * (((hashInt(Math.floor(offset / (cpuUsage ?? 1 * scale)) + (i + 20).toString() + 'dl') / 10000) % 1) ** 6) + (((hashInt(offset) / 1000) % 10) - 5)),
      })),
      gpus: range(this.host.gpus.length).map((i) => ({
        // eslint-disable-next-line max-len
        usage: gpu_usage(i),
        // eslint-disable-next-line max-len
        mem_used: clampCeil(this.host.gpus[i].vram, Math.round(128 + 0.6 * (this.host.gpus[i].vram * (((hashInt(Math.floor(offset / cpuUsage ?? 1) + (i + 20).toString() + 'gpu') / 10000) % 1) ** 10) + (gpu_usage(i) / 100 * this.host.gpus[i].vram)))),
        temp: clampCeil(105, 25 + 35 * (gpu_usage(i) / specs.gpus[i].cooler_efficency / 100)),
      })),
    };
  }

  private getFakeSignalPower(offsetRAW = 0): number {
    const scale = 5;
    const x = (offsetRAW + hashInt(this.host.name + this.host.cpuName + this.host.arch)) / (9 * Math.PI) / scale;

    const power = (((Math.sin(x - Math.sin(x))) / 0.5) + Math.cos(x / 2)) / 2.5;


    return power > 0.45 ? 3 : (power > -0.45 ? 2 : 1);
  }

  private getFakeAmbientTemp(offsetRAW = 0): number {
    const scale = 5;
    const x = (offsetRAW + hashInt(this.host.name + this.host.cpuName + this.host.arch)) / (9 * Math.PI) / scale;


    return 20 + (((Math.sin(x - Math.sin(x))) / 0.4) + Math.cos(x / 2)) / 5;
  }
}
