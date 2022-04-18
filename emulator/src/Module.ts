import { connect, MqttClient } from 'mqtt';
import { aliases } from '#shared/sensors';
import { clamp, clampCeil, hash, hashInt, padLeft, timeNow } from '#shared/utils';
import { packDataAuto } from '#shared/packets';
import { SENSOR_DATA } from '#shared/opcodes';
import { Sensors, SysInfo } from '#shared/interfaces';
import { MQTTSettings } from 'interfaces';


export default class Module {
  name: string;
  host: SysInfo;
  mqttSettings: MQTTSettings;
  client: MqttClient;

  constructor(host: SysInfo, mqttSettings: MQTTSettings) {
    this.name = `${host.name}(${hash(host.name)})`;

    this.host = host;
    this.mqttSettings = mqttSettings;

    this.client = connect(`mqtt://${this.mqttSettings.ip}`, {
      clientId: 'emu_' + hash(this.host.name),
      username: this.mqttSettings.login,
      password: this.mqttSettings.password,
    });

    this.client.subscribe('pico_in');
    this.client.subscribe('pico_out');

    this.client.on('message', this.onMessageHandler.bind(this));
  }

  private log(message: unknown, ...args: unknown[]) {
    console.log(`[${this.name}]`, message, ...args);
  }

  private onMessageHandler(topic: string, message: Buffer) {
    if (topic === 'pico_in') {
      this.log('Message to Pico:', message.toString());

      switch (message.toString()) {
        case 'power':
          this.log('Power');
          break;
        case 'reset':
          this.log('Reset');
          break;
        case 'getSensors':
          this.client.publish('pico_out', packDataAuto(SENSOR_DATA, ...Object.values(this.getFakeSensors(timeNow()))));
          break;
      }
    } else if (topic === 'pico_out') {
      this.log('Message from Pico:', message.toString());
    }
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

  private generateSensors(offset: number, scale: number): Sensors {
    const d: Sensors = {};
    const specs = this.systemSpecs;

    // eslint-disable-next-line max-len
    const batt_level = (o: number) => Math.sin(hashInt(this.host.name) + o * Math.PI / (specs.batt_capacity / (specs.batt_charge_speed / specs.batt_voltage)) / 60 / scale) * 45 + 55;
    const cpu_usage = (v: number) => clamp(0, 100, (1.02 ** (((hashInt(Math.floor(hashInt(this.host.cpuName) + offset / v)) % 5000) / 20) + 150)) / 25);


    d.batt_charge = batt_level(offset) > batt_level(offset - 1) ? specs.batt_charge_speed : 0;
    d.batt_level = batt_level(offset);
    // eslint-disable-next-line max-len
    d.batt_time = batt_level(offset) < batt_level(offset - 1) ? 60 * (specs.batt_capacity / 100 * d.batt_level) / (specs.batt_charge_speed / specs.batt_voltage) : 0;

    // eslint-disable-next-line max-len
    d.bclk = 100 - Math.max(0, Math.round(1.01 ** (hashInt(hashInt(this.host.name) + Math.floor(offset / specs.bclk_change_rate / 60)) % 650) / 10) / 10 - 0.3);

    // eslint-disable-next-line max-len
    d.cpu_usage = clampCeil(100, cpu_usage((cpu_usage(180) * (Math.floor(offset / scale)) % 240)) + ((hashInt(offset + 'cpu') % 1001) / 100));
    d.cpu_power = 15 + d.cpu_usage * specs.cpu_tdp / 100 + (((hashInt(offset / 5 + 'cpu_pow') % 101) / 10) - 5);
    d.cpu_temp = clampCeil(105, 25 + 35 * ((d.cpu_power / specs.cpu_tdp) / specs.cooler_efficency));

    d.cpu_fan = clampCeil(specs.fan_rpm, Math.round(d.cpu_temp / 95 * specs.fan_rpm));

    // eslint-disable-next-line max-len
    d.ram_used = clampCeil(Math.ceil(this.host.ramTotal / 1_048_576), Math.round(((2048 + (((1.002 ** (((hashInt(hashInt(this.host.cpuName) + Math.floor(offset / 360)) % 1500) + 2000)))) / 1200) * this.host.ramTotal) + (d.cpu_usage / 100 * this.host.ramTotal)) / 1_048_576));
    d.ram_freq = 1200 + hashInt(this.host.name + 'freq') % 10 * 200;


    return d;
  }


  private getFakeSensors(offsetRAW = 0): Sensors {
    const scale = 60;
    const offset = offsetRAW + hashInt(this.host.name + this.host.cpuName + this.host.arch);


    const sensors = this.generateSensors(offset, scale);
    const specs = this.systemSpecs;
    const d: Sensors = {};

    for (const k of Object.keys(aliases).sort()) {
      if (k.startsWith('_')) continue;
      if (sensors[k] === undefined) this.log('[Warning] Undefined sensor:', k);

      d[k] = sensors[k] ?? -1;
    }

    // system state:
    let remCpu: number = d.cpu_usage ?? 0;

    for (let i = 0; i < this.host.cpuThreads; i += 1) {
      const usage = clampCeil(100, remCpu) * (((hashInt(offset * (i + 20) + 'core') / 10000) % 1) ** 3.5);
      remCpu -= usage / this.host.cpuThreads;

      d[`cpu${padLeft(i, 2, '0')}_usage`] = usage;
    }

    while (remCpu > 0.001) {
      for (let i = 0; i < this.host.cpuThreads; i += 1) {
        const topup = clampCeil(100 - d[`cpu${padLeft(i, 2, '0')}_usage`], remCpu);
        remCpu -= topup / this.host.cpuThreads;

        d[`cpu${padLeft(i, 2, '0')}_usage`] += topup;
      }
    }


    for (let i = 0; i < this.host.drives.length; i += 1) {
      // eslint-disable-next-line max-len
      d[`drive${i}_read`] = clamp(0, specs.drives[i].max_read, specs.drives[i].max_read * (((hashInt(Math.floor(offset / scale) + (i + 20).toString() + 'drive_read') / 10000) % 1) ** 10) + (((hashInt(offset) / 1000) % 10) - 5));
      // eslint-disable-next-line max-len
      d[`drive${i}_write`] = clamp(0, specs.drives[i].max_write, specs.drives[i].max_write * (((hashInt(Math.floor(offset / scale) + (i + 20).toString() + 'drive_write') / 10000) % 1) ** 12) + (((hashInt(offset) / 1000) % 10) - 5));
    }

    for (let i = 0; i < this.host.drives.length; i += 1) {
      d[`smart${i}_usage`] = Math.max(d[`drive${i}_read`] / specs.drives[i].max_read * 100, d[`drive${i}_write`] / specs.drives[i].max_write * 100);
      d[`smart${i}_life`] = specs.drives[i].has_life ? specs.drives[i].starting_life - Math.floor(offsetRAW / 360 / scale) : -1;
      d[`smart${i}_warning`] = 0;
      d[`smart${i}_failure`] = 0;
      d[`smart${i}_reads`] = specs.drives[i].starting_reads + Math.floor(offsetRAW / 30 / scale);
      d[`smart${i}_writes`] = specs.drives[i].starting_writes + Math.floor(offsetRAW / 30 / scale);
    }

    for (let i = 0; i < this.host.networkInterfaces.length; i += 1) {
      // eslint-disable-next-line max-len
      d[`net${i}_up`] = clamp(0, specs.networkInterfaces[i].max_up, specs.networkInterfaces[i].max_up * (((hashInt(Math.floor(offset / (d.cpu_usage ?? 1 * scale)) + (i + 20).toString() + 'up') / 10000) % 1) ** 10) + (((hashInt(offset) / 1000) % 10) - 5));
      // eslint-disable-next-line max-len
      d[`net${i}_dl`] = clamp(0, specs.networkInterfaces[i].max_dl, specs.networkInterfaces[i].max_dl * (((hashInt(Math.floor(offset / (d.cpu_usage ?? 1 * scale)) + (i + 20).toString() + 'dl') / 10000) % 1) ** 6) + (((hashInt(offset) / 1000) % 10) - 5));
    }

    for (let i = 0; i < this.host.gpus.length; i += 1) {
      // eslint-disable-next-line max-len
      d[`gpu${i}_usage`] = clamp(0, 100, (1.02 ** (((hashInt(Math.floor(hashInt(this.host.gpus[i].name) + Math.floor(offset / scale))) % 5000) / 20) + 150)) / 25 + ((hashInt(offset + this.host.cpuName) % 1001) / 100));
      // eslint-disable-next-line max-len
      d[`gpu${i}_mem_used`] = clampCeil(this.host.gpus[i].vram, Math.round(128 + 0.6 * (this.host.gpus[i].vram * (((hashInt(Math.floor(offset / d.cpu_usage ?? 1) + (i + 20).toString() + 'gpu') / 10000) % 1) ** 10) + (d[`gpu${i}_usage`] / 100 * this.host.gpus[i].vram))));
      d[`gpu${i}_temp`] = clampCeil(105, 25 + 35 * (d[`gpu${i}_usage`] / specs.gpus[i].cooler_efficency / 100));
    }


    return d;
  }

  private getFakeSignalPower(offsetRAW = 0): number {
    const scale = 5;
    const x = (offsetRAW + hashInt(this.host.name + this.host.cpuName + this.host.arch)) / (9 * Math.PI) / scale;

    const power = (((Math.sin(x - Math.sin(x))) / 0.5) + Math.cos(x / 2)) / 2.5;


    return power > 0.45 ? 3 : (power > -0.45 ? 2 : 1);
  }
}
