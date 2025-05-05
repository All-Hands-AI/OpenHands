// Simple logger utility to centralize logging and make it easier to disable in production
const isDev = import.meta.env.DEV;

export const logger = {
  log: (message: string, ...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.log(message, ...args);
    }
  },
  
  error: (message: string, ...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.error(message, ...args);
    }
  },
  
  warn: (message: string, ...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.warn(message, ...args);
    }
  },
  
  info: (message: string, ...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.info(message, ...args);
    }
  },
};