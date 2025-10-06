import { OpenHandsAction } from "./actions";
import { OpenHandsObservation } from "./observations";
import { OpenHandsVariance } from "./variances";

/**
 * @deprecated use the v1 OpenHandsEvent instead
 */
export type OpenHandsParsedEvent =
  | OpenHandsAction
  | OpenHandsObservation
  | OpenHandsVariance;
