import { arrayFrom } from '#shared/utils';
import { InvalidParams, ModuleNotFound, RequestTimeout, UnsuportedOpcode } from '../errors';
import { Router } from 'express';
import { getHDDActivity, getPowerStatus } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/power', async (req, res) => {
  try {
    const target = arrayFrom(req.query.module);
    const data: { name: string; data: number; }[] = [];

    await Promise.all(
      target.map(async (module) => {
        // validate arguments
        if (typeof module !== 'string' && module !== undefined) throw new InvalidParams('Module name must be a string');

        // unwrap data
        data.push(...(await getPowerStatus(module)));
      }),
    );

    res.json({ data: data });
  } catch (err) {
    res.contentType('text/plain');

    if (err instanceof UnsuportedOpcode) res.status(501).send(err.message);
    else if (err instanceof ModuleNotFound) res.status(404).send(err.message);
    else if (err instanceof RequestTimeout) res.status(504).send(err.message);
    else if (err instanceof InvalidParams) res.status(400).json(err.message);
    else res.sendStatus(500);
  }
});

router.get('/hdd', async (req, res) => {
  try {
    const target = arrayFrom(req.query.module);
    const data: { name: string; data: number[]; }[] = [];

    await Promise.all(
      target.map(async (module) => {
        // validate arguments
        if (typeof module !== 'string' && module !== undefined) throw new InvalidParams('Module name must be a string');

        // unwrap data
        data.push(...(await getHDDActivity(module)));
      }),
    );

    res.json({ data: data });
  } catch (err) {
    res.contentType('text/plain');

    if (err instanceof UnsuportedOpcode) res.status(501).send(err.message);
    else if (err instanceof ModuleNotFound) res.status(404).send(err.message);
    else if (err instanceof RequestTimeout) res.status(504).send(err.message);
    else if (err instanceof InvalidParams) res.status(400).json(err.message);
    else res.sendStatus(500);
  }
});
