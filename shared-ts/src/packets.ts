import { Opcodes, PACKET_STOP } from './opcodes';
import struct, { DataType } from 'python-struct';


export const packData = (opcode: Opcodes, packetFormat: string, ...data: unknown[]): Buffer => {
  let headerSize = packetFormat.length + 2;
  headerSize += Math.floor(Math.log10(headerSize)) + 2;

  const finalFormat = `B${headerSize}s` + packetFormat;
  const packet = struct.pack(finalFormat, opcode, finalFormat, ...data as DataType[]);


  return Buffer.concat([packet, PACKET_STOP]);
};

export const packDataAuto = (opcode: Opcodes, ...data: unknown[]): Buffer => {
  let packetFormat = '';

  for (const d of data) {
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


  return packData(opcode, packetFormat, ...data);
};

export const unpackData = (packet: Buffer): [number, string, ...unknown[]] => {
  const opcode = packet[0];
  const headerSize = parseInt(packet.subarray(2, packet.indexOf('s')).toString());
  const header = packet.subarray(1, headerSize + 1).toString();
  const data = struct.unpack(header, packet.subarray(0, -PACKET_STOP.length)) as [number, string, ...unknown[]];

  // console.log(opcode);
  // console.log(headerSize);
  // console.log(header);
  // console.log(data);


  return data;
};

export const createRequest = (request: number): Buffer => packData(request, '');
