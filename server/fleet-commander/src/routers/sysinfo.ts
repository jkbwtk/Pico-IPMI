import { Router } from 'express';
import { getSysInfo } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', async (req, res) => {
  try {
    const sysinfo = await getSysInfo();
    res.json(sysinfo);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});

router.get('/:name', async (req, res) => {
  try {
    const sysinfo = await getSysInfo(req.params.name);
    res.json(sysinfo);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
