require('module-alias/register');

import config from './config';
import express from 'express';
import { invalidRoute, logger } from './middlewares';
import moduleRouter from './routers/modules';
import sensorRouter from './routers/sensors';
import sysinfoRouter from './routers/sysinfo';


const api = express();


api.use(logger);
api.use('/modules', moduleRouter);
api.use('/sensors', sensorRouter);
api.use('/sysinfo', sysinfoRouter);

api.use(invalidRoute);


api.listen(config.api.port);
