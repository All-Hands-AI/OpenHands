import { GetConfigResponse } from "#/api/open-hands.types";

declare global {
  interface Window {
    __OPENHANDS_CONFIG__?: GetConfigResponse;
  }
}