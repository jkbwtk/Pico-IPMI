import { RequestHandler } from 'express';

export const logger: RequestHandler = (req, res, next) => {
  console.log(req.method, req.url, req.hostname);
  next();
};

export const invalidRoute: RequestHandler = (req, res) => {
  res.status(404).json('Invalid Route');
};
