import { Router } from 'express';
import { getModule } from '../mqttHandler';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.get('/', (req, res) => {
  res.json(getModule());
});

router.get('/:name', (req, res) => {
  try {
    const module = getModule(req.params.name);
    res.json(module);
  } catch (err) {
    res.status(400).json('Module not found');
  }
});


