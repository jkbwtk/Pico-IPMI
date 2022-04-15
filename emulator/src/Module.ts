import { Host, MQTTSettings } from './interfaces';
import { connect, MqttClient } from 'mqtt';
import { hash } from './utils';


export default class Module {
  host: Host;
  mqttSettings: MQTTSettings;
  client: MqttClient;

  constructor(host: Host, mqttSettings: MQTTSettings) {
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

  private onMessageHandler(topic: string, message: Buffer) {
    console.log(topic, message);
  }
}
