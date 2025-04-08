import { DevAction } from "./actions";
import { DevObservation } from "./observations";
import { DevVariance } from "./variances";

export type DevParsedEvent =
  | DevAction
  | DevObservation
  | DevVariance;
