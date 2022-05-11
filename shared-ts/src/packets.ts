import { Opcodes, PACKET_STOP } from './opcodes';
import struct, { DataType } from 'python-struct';
import { Routes } from './routes';
import { Packet } from './interfaces';


export const packDataRaw = (packetFormat: string, ...data: DataType[]): Buffer => {
  let headerSize = packetFormat.length + 1;
  headerSize += headerSize.toString().length;

  // fix for sizes 11, 101, 102, 1001, 1002, 1003, etc.
  while (headerSize < (`${headerSize}s` + packetFormat).length) headerSize += 1;

  const finalFormat = `${headerSize}s` + packetFormat;
  const packet = struct.pack(finalFormat, finalFormat, ...data as DataType[]);


  return Buffer.concat([packet, PACKET_STOP]);
};


type PackData = (opcode: Opcodes, origin: Routes, destination: Routes, uniq: number, channel: Routes, ...data: DataType[]) => Buffer;

export const packData: PackData = (...args): Buffer => {
  let packetFormat = '';

  for (const d of args) {
    if (typeof d == 'number') {
      if (d % 1 === 0) {
        if (d < 256 && d >= 0) {
          packetFormat += 'B';
        } else if (d < 127 && d >= -128) {
          packetFormat += 'b';
        } else if (d < 65536 && d >= 0) {
          packetFormat += 'H';
        } else if (d < 32767 && d >= -32768) {
          packetFormat += 'h';
        } else {
          packetFormat += 'i';
        }
      } else {
        packetFormat += 'f';
      }
    } else if (typeof d === 'boolean') {
      packetFormat += 'h';
    } else {
      packetFormat += `${`${d}`.length}s`;
    }
  }

  return packDataRaw(packetFormat, ...args);
};

export const unpackDataRaw = (packet: Buffer): DataType[] => {
  const headerSize = parseInt(packet.subarray(0, packet.indexOf('s')).toString());
  const header = packet.subarray(0, headerSize).toString();
  const data = struct.unpack(header, packet.subarray(0, -PACKET_STOP.length));

  // console.log(opcode);
  // console.log(headerSize);
  // console.log(header);
  // console.log(data);


  return data;
};

export const unpackData = (packet: Buffer): Packet => {
  const data = unpackDataRaw(packet);

  if (data.length < 6) throw new Error('Invalid packet, too few arguments');

  if (typeof data[1] !== 'number') throw new Error('Invalid packet, opcode is not a number');
  if (typeof data[2] !== 'number') throw new Error('Invalid packet, origin is not a number');
  if (typeof data[3] !== 'number') throw new Error('Invalid packet, destination is not a number');
  if (typeof data[4] !== 'number') throw new Error('Invalid packet, uniq is not a number');
  if (typeof data[5] !== 'number') throw new Error('Invalid packet, channel is not a number');

  const opcode = data[1];
  const origin = data[2];
  const destination = data[3];
  const uniq = data[4];
  const channel = data[5];

  return { opcode, origin, destination, uniq, channel, data: data.slice(6) };
};
