import Ajv from 'ajv';
import { join } from 'path';
import { loadJSON } from '#shared/utils';
import { configSchema } from './schemas';
import { Config } from 'interfaces';


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
