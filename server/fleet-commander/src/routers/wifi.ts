import { Router } from 'express';
import { getWiFi } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', async (req, res) => {
  try {
    const power = await getWiFi();
    res.json(power);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});

router.get('/:name', async (req, res) => {
  try {
    const power = await getWiFi(req.params.name);
    res.json(power);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
