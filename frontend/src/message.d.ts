import { PayloadAction } from "@reduxjs/toolkit"
import { OpenHandsAction } from "./types/core/actions"
import { OpenHandsObservation } from "./types/core/observations"

export type Message = {
  sender: "user" | "assistant"
  content: string
  timestamp: string
  imageUrls?: string[]
  type?: "thought" | "error" | "action" | "customAction"
  success?: boolean
  pending?: boolean
  translationID?: string
  eventID?: number
  messageActionID?: string
  observation?: PayloadAction<OpenHandsObservation>
  action?: PayloadAction<OpenHandsAction>
}
