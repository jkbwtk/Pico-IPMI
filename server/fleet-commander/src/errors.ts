import { Opcodes } from '#shared/opcodes';

export class InvalidParams extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InvalidParams';
  }
}

export class InternalError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InternalError';
  }
}

export class UnsuportedOpcode extends Error {
  constructor(opcode: Opcodes) {
    super(`Unsuported Opcode: ${opcode}`);
    this.name = 'UnsuportedOpcode';
  }
}

export class ModuleNotFound extends Error {
  constructor(module: string) {
    super(`Module ${module} Not Found`);
    this.name = 'ModuleNotFound';
  }
}

export class RequestTimeout extends Error {
  constructor(uniq: number) {
    super(`Request ${uniq} Timed Out`);
    this.name = 'RequestTimeout';
  }
}
