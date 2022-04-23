import { JSONSchemaType } from 'ajv';
import { Config } from 'interfaces';


export const configSchema: JSONSchemaType<Config> = {
  type: 'object',
  properties: {
    mqtt: {
      type: 'object',
      properties: {
        ip: { type: 'string' },
        login: { type: 'string', default: '' },
        password: { type: 'string', default: '' },
        requestRetries: { type: 'number', minimum: 0, default: 5 },
        requestTimeout: { type: 'number', minimum: 1, default: 1000 },
      },
      required: ['ip'],
    },
    api: {
      type: 'object',
      default: { port: 8080 },
      properties: {
        port: { type: 'number', minimum: 1, maximum: 65536, default: 8080 },
      },
      required: [],
    },
  },
  required: ['mqtt'],
  additionalProperties: true,
};
