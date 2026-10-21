export interface ConfirmationResponseRequest {
  accept: boolean;
  reason?: string;
}

export interface ConfirmationResponseResponse {
  success: boolean;
}

export type EventSortOrder = "TIMESTAMP" | "TIMESTAMP_DESC";

/**
 * Which copy of a conversation's event log to read. On Cloud the runtime
 * sandbox holds the log and the App API holds a webhook-fed copy of it that
 * can lag. Local backends only have the runtime.
 */
export type EventLogSource = "runtime" | "app-api";

export interface EventSearchOptions {
  /** Maximum number of events to return per page (server caps at 100). */
  limit?: number;
  /** Page ID for pagination. */
  pageId?: string;
  /** Sort order for the underlying server query. */
  sortOrder?: EventSortOrder;
  /** Filter: event timestamp >= this value (ISO 8601). */
  timestampGte?: string;
  /** Filter: event timestamp < this value (ISO 8601). */
  timestampLt?: string;
  /**
   * Surface unsupported cloud pagination instead of degrading to an empty
   * page. Callers that require a complete result (such as transcript export)
   * must set this so a partial history is never mistaken for exhaustion.
   */
  strictPagination?: boolean;
  /**
   * Log to read on Cloud. Defaults to `"app-api"`, which outlives the
   * sandbox. Ignored on Local backends, which always read the runtime.
   */
  source?: EventLogSource;
}

export interface EventSearchPage<TEvent> {
  items: TEvent[];
  next_page_id?: string | null;
}
