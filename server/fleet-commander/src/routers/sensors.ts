import { Router } from 'express';
import { getSensors } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', async (req, res) => {
  try {
    const sensors = await getSensors();
    res.json(sensors);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});

router.get('/:name', async (req, res) => {
  try {
    const sensors = await getSensors(req.params.name);
    res.json(sensors);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
