import { createHash } from 'crypto';
import { readFileSync } from 'fs';
import path from 'path';


export const loadJSON = <T>(path: string): T => {
  try {
    const raw = readFileSync(path, 'utf8');
    const data = JSON.parse(raw);

    return data as T;
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
};

export const hash = (data: string): string => {
  const hash = createHash('sha256');
  hash.update(data);
  return hash.digest('hex').substring(0, 6);
};

export const hashInt = (seed: number | string): number => {
  return parseInt(hash(`${seed}`), 16);
};

export const padLeft = (val: number, len: number, pad: string): string => {
  let s = val.toString();

  while (s.length < len) {
    s = pad + s;
  }

  return s;
};

export const clamp = (min: number, max: number, val: number): number => {
  if (val < min) return min;
  if (val > max) return max;
  return val;
};

export const clampFloor = (floor: number, val: number): number => {
  if (val < floor) return floor;
  return val;
};

export const clampCeil = (ceil: number, val: number): number => {
  if (val > ceil) return ceil;
  return val;
};

export const timeNow = (): number => {
  return Math.floor(Date.now() / 1000);
};

export const getUniq = (): number => {
  return Math.floor(Math.random() * 65536);
};

export const sleep = async (time: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, time));
};


type Range = {
  (end: number): number[];
  (start: number, end: number): number[];
  (start: number, end: number, step: number): number[];
};

export const range: Range = (start, end?, step = 1): number[] => {
  const s = end !== undefined ? start : 0;
  const e = end !== undefined ? end as number : start;
  const r = [];

  if (e > s) for (let i = s; i < e; i += Math.abs(step as number)) r.push(i);
  if (s > e) for (let i = s; i > e; i -= Math.abs(step as number)) r.push(i);

  return r;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const flatten = (target: any): any[] => {
  const r = [];

  if (Array.isArray(target)) {
    for (const item of target) r.push(...flatten(item));
  } else if (typeof target === 'object') {
    for (const value of Object.values(target)) r.push(...flatten(value));
  } else {
    r.push(target);
  }

  return r;
};

export const extractFilename = (file: string): string => {
  const filename = path.basename(file);
  return filename.substring(0, filename.length - path.extname(file).length);
};

export const arrayFrom = <T>(variable: T[] | T): T[] => {
  return Array.isArray(variable) ? variable.slice() : [variable];
};
