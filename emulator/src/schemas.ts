import { JSONSchemaType } from 'ajv';
import { Config } from './interfaces';

export const configSchema: JSONSchemaType<Config> = {
  type: 'object',
  properties: {
    mqtt: {
      type: 'object',
      properties: {
        ip: { type: 'string' },
        login: { type: 'string', default: '' },
        password: { type: 'string', default: '' },
      },
      required: ['ip'],
    },
    hosts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          arch: { type: 'string' },
          cpuCores: { type: 'number', minimum: 1 },
          cpuName: { type: 'string' },
          cpuThreads: { type: 'number', minimum: 1 },
          drives: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
              },
              required: ['name'],
            },
          },
          gpus: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
                vram: { type: 'number', minimum: 1 },
              },
              required: ['name', 'vram'],
            },
          },
          name: { type: 'string' },
          networkInterfaces: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
              },
              required: ['name'],
            },
          },
          os: { type: 'string' },
          ramTotal: { type: 'number', minimum: 1 },
        },
        required: ['arch', 'cpuCores', 'cpuName', 'cpuThreads', 'drives', 'gpus', 'name', 'networkInterfaces', 'os', 'ramTotal'],
      },
    },
  },
  required: ['hosts', 'mqtt'],
  additionalProperties: false,
};
