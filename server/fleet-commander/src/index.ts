require('module-alias/register');

import config from './config';
import express from 'express';
import { accessControl, invalidRoute, logger } from './middlewares';
import v1Router from './routers/v1';
import { readdirSync } from 'fs';
import { join } from 'path';
import { extractFilename } from '#shared/utils';
import { Express } from 'express-serve-static-core';


const loadRoutes = async (api: Express) => {
  const files = readdirSync(join(__dirname, 'routers'))
    .filter((file) => file.endsWith('.js'));


  const routes = Promise.all(files.map(async (file) => {
    const module = await import(join(__dirname, 'routers', file));
    const route = '/' + extractFilename(file);

    console.log(module);
    api.use(route, module.default);

    return route;
  }));


  return routes;
};


const main = async () => {
  const api = express();


  api.use(logger);
  api.use(accessControl);

  api.use('/v1', v1Router);

  api.use(invalidRoute);


  api.listen(config.api.port);
};


main();
