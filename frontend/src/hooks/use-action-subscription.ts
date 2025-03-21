import { useEffect, useRef } from "react";
import { OpenHandsEventType } from "#/types/core/base";
import { OpenHandsAction } from "#/types/core/actions";
import { ActionMessage } from "#/types/message";
import ActionType from "#/types/action-type";

type ActionCallback = (action: OpenHandsAction | ActionMessage) => void;

// Map to store subscribers
const subscribers = new Map<string, Set<ActionCallback>>();

// Function to convert ActionType enum to OpenHandsEventType string
const convertActionType = (type: ActionType): OpenHandsEventType =>
  type.toLowerCase() as OpenHandsEventType;

/**
 * Middleware function to be called when an action is processed
 * This will notify all subscribers of the action
 */
export const notifyActionSubscribers = (
  action: OpenHandsAction | ActionMessage,
): void => {
  if (!action || !action.action) return;

  const actionType = action.action;
  const subscriberSet = subscribers.get(actionType);

  if (subscriberSet) {
    subscriberSet.forEach((callback) => {
      try {
        callback(action);
      } catch (error) {
        // Silent error handling to prevent crashes
      }
    });
  }

  // Also notify subscribers who are listening to all actions
  const allSubscribers = subscribers.get("*");
  if (allSubscribers) {
    allSubscribers.forEach((callback) => {
      try {
        callback(action);
      } catch (error) {
        // Silent error handling to prevent crashes
      }
    });
  }
};

/**
 * Hook to subscribe to specific action types
 * @param actionTypes Array of action types to subscribe to, or '*' for all actions
 * @param callback Function to call when an action of the specified type is received
 */
export const useActionSubscription = (
  actionTypes:
    | (ActionType | OpenHandsEventType | "*")[]
    | ActionType
    | OpenHandsEventType
    | "*",
  callback: ActionCallback,
): void => {
  // Create a stable reference to the callback
  const callbackRef = useRef(callback);

  // Update the callback reference when it changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    // Convert to array if not already
    const types = Array.isArray(actionTypes) ? actionTypes : [actionTypes];

    // Convert ActionType enum values to OpenHandsEventType strings if needed
    const normalizedTypes = types.map((type) => {
      if (type === "*") return type;
      return typeof type === "string" ? type : convertActionType(type);
    });

    // Subscribe to each action type
    normalizedTypes.forEach((type) => {
      if (!subscribers.has(type)) {
        subscribers.set(type, new Set());
      }

      const subscriberSet = subscribers.get(type)!;
      const wrappedCallback = (action: OpenHandsAction | ActionMessage) =>
        callbackRef.current(action);
      subscriberSet.add(wrappedCallback);

      return () => {
        // Cleanup: remove the subscription when the component unmounts
        const set = subscribers.get(type);
        if (set) {
          set.delete(wrappedCallback);
          if (set.size === 0) {
            subscribers.delete(type);
          }
        }
      };
    });

    // Return a cleanup function that unsubscribes from all types
    return () => {
      normalizedTypes.forEach((type) => {
        const set = subscribers.get(type);
        if (set) {
          const wrappedCallback = (action: OpenHandsAction | ActionMessage) =>
            callbackRef.current(action);
          set.delete(wrappedCallback);
          if (set.size === 0) {
            subscribers.delete(type);
          }
        }
      });
    };
  }, [actionTypes]); // Only re-run if actionTypes changes
};
