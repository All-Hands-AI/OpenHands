import { setupWorker } from "msw/browser";
import { handlers as wsHandlers } from "./handlers.ws";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers, ...wsHandlers);
