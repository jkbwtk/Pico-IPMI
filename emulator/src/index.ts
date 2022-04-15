import Module from './Module';
import { loadConfig } from './configLoader';
import { hash } from './utils';


const config = loadConfig();
const modules = new Map<string, Module>();


for (const host of config.hosts) {
  const module = new Module(host, config.mqtt);
  modules.set(hash(host.name), module);

  console.log(`Created: ${host.name}(${hash(host.name)})`);
}
