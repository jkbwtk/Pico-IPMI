import { ModuleNotFound, RequestTimeout, UnsuportedOpcode } from '../errors';
import { Router } from 'express';
import { postPower, postReset, postSleep } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.post('/power/:name', async (req, res) => {
  try {
    await postPower(req.params.name);
    res.sendStatus(200);
  } catch (err) {
    res.contentType('text/plain');

    if (err instanceof UnsuportedOpcode) res.status(501).send(err.message);
    else if (err instanceof ModuleNotFound) res.status(404).send(err.message);
    else if (err instanceof RequestTimeout) res.status(504).send(err.message);
    else res.sendStatus(500);
  }
});


router.post('/reset/:name', async (req, res) => {
  try {
    await postReset(req.params.name);
    res.sendStatus(200);
  } catch (err) {
    res.contentType('text/plain');

    if (err instanceof UnsuportedOpcode) res.status(501).send(err.message);
    else if (err instanceof ModuleNotFound) res.status(404).send(err.message);
    else if (err instanceof RequestTimeout) res.status(504).send(err.message);
    else res.sendStatus(500);
  }
});


router.post('/sleep/:name', async (req, res) => {
  try {
    await postSleep(req.params.name);
    res.sendStatus(200);
  } catch (err) {
    res.contentType('text/plain');

    if (err instanceof UnsuportedOpcode) res.status(501).send(err.message);
    else if (err instanceof ModuleNotFound) res.status(404).send(err.message);
    else if (err instanceof RequestTimeout) res.status(504).send(err.message);
    else res.sendStatus(500);
  }
});
