import { Router } from 'express';
import { getPowerStatus } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', async (req, res) => {
  try {
    const status = await getPowerStatus();
    res.json(status);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});

router.get('/:name', async (req, res) => {
  try {
    const status = await getPowerStatus(req.params.name);
    res.json(status);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
