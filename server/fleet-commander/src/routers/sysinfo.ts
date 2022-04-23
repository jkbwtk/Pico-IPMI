import { Router } from 'express';
import { getSysInfo } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', async (req, res) => {
  try {
    const sensors = await getSysInfo();
    res.json(sensors);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});

router.get('/:name', async (req, res) => {
  try {
    const sensors = await getSysInfo(req.params.name);
    res.json(sensors);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
