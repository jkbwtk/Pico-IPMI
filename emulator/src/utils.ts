import { createHash } from 'crypto';
import { readFileSync } from 'fs';


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

export const padLeft = (val: number, len: number, pad: string): string => {
  let s = val.toString();

  while (s.length < len) {
    s = pad + s;
  }

  return s;
};
