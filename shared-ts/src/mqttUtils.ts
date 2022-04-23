export const PUBLIC_OUT = 'public/out';
export const PUBLIC_IN = 'public/in';

export const picoOut = (module: string): string => `pico/${module}/out`;
export const picoIn = (module: string): string => `pico/${module}/in`;


export const reverseTopic = (topic: string): string => {
  if (topic === PUBLIC_OUT) return PUBLIC_IN;
  if (topic === PUBLIC_IN) return PUBLIC_OUT;

  const [, module, direction] = topic.split('/');
  return direction === 'out' ? picoIn(module) : picoOut(module);
};

export const extractModuleName = (topic: string): string => {
  const [channel, module] = topic.split('/');

  if (channel === 'public') return '';
  return module;
};
