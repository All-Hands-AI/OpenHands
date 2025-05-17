import { PayloadAction } from "@reduxjs/toolkit";
import { OpenHandsObservation } from "./types/core/observations";
import { OpenHandsAction } from "./types/core/actions";

export type Message = {
  sender: "user" | "assistant";
  content: string;
  timestamp: string;
  imageUrls?: string[]; // Keep this for user messages with images
  type?: "thought" | "error" | "action";
  success?: boolean;
  pending?: boolean;
  translationID?: string;
  eventID?: number;
  observation?: PayloadAction<OpenHandsObservation>;
  action?: PayloadAction<OpenHandsAction>;
};
