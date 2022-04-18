require('module-alias/register');

import Module from './Module';
import { loadConfig } from './configLoader';
import { hash } from '#shared/utils';


const config = loadConfig();
const modules = new Map<string, Module>();


for (const host of config.hosts) {
  const module = new Module(host, config.mqtt);
  modules.set(hash(host.name), module);

  console.log(`Created: ${module.name}`);
}
