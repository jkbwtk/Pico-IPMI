import { Router } from 'express';
import { getHDDActivity } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', async (req, res) => {
  try {
    const activity = await getHDDActivity();
    res.json(activity);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});

router.get('/:name', async (req, res) => {
  try {
    const activity = await getHDDActivity(req.params.name);
    res.json(activity);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
