import { QueryClient } from "@tanstack/react-query";
import {
  initQueryReduxBridge,
  getQueryReduxBridge,
  SliceNames,
} from "./utils/query-redux-bridge";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the bridge
export function initializeBridge() {
  console.log("[DOUBLE_MSG_DEBUG] QueryReduxBridge initializing bridge");
  // Initialize the bridge with the query client
  initQueryReduxBridge(queryClient);

  // Mark slices as migrated to React Query
  getQueryReduxBridge().migrateSlice("status");
  getQueryReduxBridge().migrateSlice("metrics");
  getQueryReduxBridge().migrateSlice("initialQuery");
  getQueryReduxBridge().migrateSlice("browser");
  getQueryReduxBridge().migrateSlice("code");
  getQueryReduxBridge().migrateSlice("fileState");
  getQueryReduxBridge().migrateSlice("command");
  getQueryReduxBridge().migrateSlice("jupyter");
  getQueryReduxBridge().migrateSlice("agent");
  // IMPORTANT: We are NOT migrating the chat slice for now
  // Keeping it in Redux until we fix the double message issue
  console.log("[DOUBLE_MSG_DEBUG] QueryReduxBridge NOT migrating chat slice - keeping in Redux");
  // getQueryReduxBridge().migrateSlice("chat");
  getQueryReduxBridge().migrateSlice("securityAnalyzer");
}

// Export a function to check if a slice is migrated
export function isSliceMigrated(sliceName: SliceNames) {
  try {
    const isMigrated = getQueryReduxBridge().isSliceMigrated(sliceName);
    if (sliceName === "chat") {
      console.log("[DOUBLE_MSG_DEBUG] isSliceMigrated check for chat:", {
        isMigrated,
        timestamp: new Date().toISOString()
      });
    }
    return isMigrated;
  } catch (error) {
    // If the bridge is not initialized, return false
    if (sliceName === "chat") {
      console.log("[DOUBLE_MSG_DEBUG] isSliceMigrated check for chat failed:", {
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString()
      });
    }
    return false;
  }
}
