import { Router } from 'express';
import { getAmbientTemp } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', async (req, res) => {
  try {
    const temp = await getAmbientTemp();
    res.json(temp);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});

router.get('/:name', async (req, res) => {
  try {
    const temp = await getAmbientTemp(req.params.name);
    res.json(temp);
  } catch (err) {
    res.status(400).json('MQTT request timed out');
  }
});
