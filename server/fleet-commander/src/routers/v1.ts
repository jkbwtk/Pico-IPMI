import { Router } from 'express';
import moduleRouter from './modules';
import sensorsRouter from './sensors';
import ledsRouter from './leds';
import commandsRouter from './commands';

// eslint-disable-next-line new-cap
const router = Router();
export default router;


router.use('/sensors', sensorsRouter);
router.use('/modules', moduleRouter);
router.use('/commands', commandsRouter);
router.use('/leds', ledsRouter);
