import Ajv from 'ajv';
import { join } from 'path';
import { loadJSON } from './utils';
import { Config } from './interfaces';
import { configSchema } from './schemas';


const ajv = new Ajv({ useDefaults: true });
const configValidator = ajv.compile(configSchema);


export const loadConfig = (): Config => {
  try {
    const config = loadJSON(join(__dirname, '..', 'settings.json'));

    if (configValidator(config)) {
      return config;
    } else {
      throw new Error(`Invalid config: ${JSON.stringify(configValidator.errors, null, 2)}`);
    }
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
};
