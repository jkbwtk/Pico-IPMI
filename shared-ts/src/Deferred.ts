/* eslint-disable @typescript-eslint/no-empty-function */


export default class Deferred<T> {
  promise: Promise<T>;
  public resolve: (value: T | PromiseLike<T>) => void = () => { };
  public reject: (reason?: Error) => void = () => { };

  constructor() {
    this.promise = new Promise((resolve, reject) => {
      this.resolve = resolve;
      this.reject = reject;
    });
  }
}
