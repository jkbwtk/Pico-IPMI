import { RequestHandler } from 'express';

export const logger: RequestHandler = (req, res, next) => {
  console.log(req.method, req.url, req.hostname);
  next();
};

export const invalidRoute: RequestHandler = (req, res) => {
  res.contentType('text/plain');
  res.status(404).send('Invalid Route');
};

export const accessControl: RequestHandler = (req, res, next) => {
  res.header('Access-Control-Allow-Origin', req.header('Origin') || '*');
  res.header('Vary', 'Origin');

  next();
};

export const notImplemented: RequestHandler = (req, res) => {
  res.sendStatus(501);
};
