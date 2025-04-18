import { OpenHandsAction } from "./actions";
import { OpenHandsObservation } from "./observations";
import { OpenHandsVariance } from "./variances";

export type OpenHandsParsedEvent =
  | OpenHandsAction
  | OpenHandsObservation
  | OpenHandsVariance;
