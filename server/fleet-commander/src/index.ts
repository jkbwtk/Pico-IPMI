require('module-alias/register');

import config from './config';
import express from 'express';
import { invalidRoute, logger } from './middlewares';
import moduleRouter from './routers/modules';
import sensorRouter from './routers/sensors';
import sysinfoRouter from './routers/sysinfo';
import wifiRouter from './routers/wifi';
import powerStatusRouter from './routers/powerStatus';
import hddActivityRouter from './routers/hddActivity';
import powerRouter from './routers/power';
import resetRouter from './routers/reset';
import sleepRouter from './routers/sleep';
import ambientTempRouter from './routers/ambientTemp';

const api = express();


api.use(logger);
api.use('/modules', moduleRouter);
api.use('/sensors', sensorRouter);
api.use('/sysinfo', sysinfoRouter);
api.use('/wifi', wifiRouter);
api.use('/powerstatus', powerStatusRouter);
api.use('/hddactivity', hddActivityRouter);
api.use('/power', powerRouter);
api.use('/reset', resetRouter);
api.use('/sleep', sleepRouter);
api.use('/ambientTemp', ambientTempRouter);


api.use(invalidRoute);


api.listen(config.api.port);
