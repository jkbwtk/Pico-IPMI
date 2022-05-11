import { Router } from 'express';
import { postSleep } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/:name', async (req, res) => {
  try {
    await postSleep(req.params.name);
    res.sendStatus(200);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
