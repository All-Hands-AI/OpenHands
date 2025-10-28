# History Loading State Implementation Plan

## Overview
This document outlines the implementation plan for adding history loading state detection to the V1 conversation websocket context using the `/api/v1/events/count` endpoint.

## Problem Statement
When connecting to an existing conversation, the server sends all historical events via WebSocket (`resend_all=true`). However, there's no completion marker to indicate when history loading is finished, making it difficult to show appropriate loading indicators to users.

## Solution: Count-Based Detection

Use the `/api/v1/events/count` endpoint to fetch the expected number of events, then track received events to determine when history loading is complete.

---

## API Endpoint Details

### Backend Endpoint
- **Path:** `GET /api/v1/events/count`
- **Location:** `/Users/stephan/Desktop/aha/OpenHands/openhands/app_server/event/event_router.py:68-99`

### Query Parameters
- `conversation_id__eq` (UUID) - **Required** - Filter events by conversation ID
- `kind__eq` (EventKind) - Optional - Filter by event type
- `timestamp__gte` (datetime) - Optional - Filter by timestamp >=
- `timestamp__lt` (datetime) - Optional - Filter by timestamp <
- `sort_order` (EventSortOrder) - Optional - Sort order (default: TIMESTAMP)

### Response
Returns an integer representing the count of events matching the filters.

---

## Test Coverage

### Tests Created (Currently Failing ✓)
Located in: `/Users/stephan/Desktop/aha/OpenHands/frontend/__tests__/conversation-websocket-handler.test.tsx:420-580`

1. **"should track history loading state using event count from API"**
   - Tests the main scenario with 3 historical events
   - Verifies `isLoadingHistory` starts as `true`
   - Verifies it becomes `false` after all events are received

2. **"should handle empty conversation history"**
   - Tests the edge case of a new conversation with 0 events
   - Verifies loading state transitions quickly to `false`

3. **"should handle history loading with large event count"**
   - Tests with 50 events to ensure scalability
   - Verifies proper state management with larger datasets

### Test Status
```bash
FAIL  __tests__/conversation-websocket-handler.test.tsx
  × should track history loading state using event count from API
  × should handle empty conversation history
  × should handle history loading with large event count
```
**Error:** `useConversationWebSocket is not defined` (Expected - `isLoadingHistory` not implemented yet)

---

## Implementation Steps

### 1. Add Event Count API Method
**File:** `/Users/stephan/Desktop/aha/OpenHands/frontend/src/api/conversation-service/v1-conversation-service.api.ts`

```typescript
/**
 * Get the count of events for a conversation
 * @param conversationId The conversation ID
 * @returns The number of events in the conversation
 */
static async getEventCount(conversationId: string): Promise<number> {
  const params = new URLSearchParams();
  params.append('conversation_id__eq', conversationId);

  const { data } = await openHands.get<number>(
    `/api/v1/events/count?${params.toString()}`
  );

  return data;
}
```

### 2. Create useEventCount Hook (Optional but Recommended)
**File:** `/Users/stephan/Desktop/aha/OpenHands/frontend/src/hooks/query/use-event-count.ts`

```typescript
import { useQuery } from "@tanstack/react-query";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";

export const useEventCount = (conversationId?: string) => {
  return useQuery({
    queryKey: ["eventCount", conversationId],
    queryFn: () => V1ConversationService.getEventCount(conversationId!),
    enabled: !!conversationId,
    staleTime: Infinity, // Event count for history doesn't change once fetched
    gcTime: 1000 * 60 * 5, // 5 minutes
  });
};
```

### 3. Modify ConversationWebSocketContext
**File:** `/Users/stephan/Desktop/aha/OpenHands/frontend/src/contexts/conversation-websocket-context.tsx`

#### Changes Required:

1. **Add state for history loading:**
```typescript
const [isLoadingHistory, setIsLoadingHistory] = useState(true);
const [expectedEventCount, setExpectedEventCount] = useState<number | null>(null);
const receivedEventCountRef = useRef(0);
```

2. **Fetch event count on connection open:**
```typescript
onOpen: async () => {
  setConnectionState("OPEN");
  hasConnectedRef.current = true;
  removeErrorMessage();

  // Fetch expected event count
  if (conversationId) {
    try {
      const count = await V1ConversationService.getEventCount(conversationId);
      setExpectedEventCount(count);

      // If no events expected, mark as loaded immediately
      if (count === 0) {
        setIsLoadingHistory(false);
      }
    } catch (error) {
      console.warn("Failed to fetch event count:", error);
      // Fall back to debounce-based detection or mark as loaded
      setIsLoadingHistory(false);
    }
  }
},
```

3. **Track received events in handleMessage:**
```typescript
const handleMessage = useCallback(
  (messageEvent: MessageEvent) => {
    try {
      const event = JSON.parse(messageEvent.data);

      if (isV1Event(event)) {
        addEvent(event);

        // Track received events for history loading
        if (isLoadingHistory && expectedEventCount !== null) {
          receivedEventCountRef.current += 1;

          if (receivedEventCountRef.current >= expectedEventCount) {
            setIsLoadingHistory(false);
          }
        }

        // ... rest of event handling
      }
    } catch (error) {
      console.warn("Failed to parse WebSocket message as JSON:", error);
    }
  },
  [addEvent, isLoadingHistory, expectedEventCount, /* ...other deps */],
);
```

4. **Reset state on conversation change:**
```typescript
useEffect(() => {
  hasConnectedRef.current = false;
  setIsLoadingHistory(true);
  setExpectedEventCount(null);
  receivedEventCountRef.current = 0;
}, [conversationId]);
```

5. **Update context type and value:**
```typescript
interface ConversationWebSocketContextType {
  connectionState: V1_WebSocketConnectionState;
  sendMessage: (message: V1SendMessageRequest) => Promise<void>;
  isLoadingHistory: boolean; // Add this
}

const contextValue = useMemo(
  () => ({ connectionState, sendMessage, isLoadingHistory }),
  [connectionState, sendMessage, isLoadingHistory],
);
```

### 4. Update ChatInterface (Optional)
**File:** `/Users/stephan/Desktop/aha/OpenHands/frontend/src/components/features/chat/chat-interface.tsx:225-229`

Replace V0-only loading check with V1-aware version:
```typescript
const { isLoadingHistory: isV1LoadingHistory } = useConversationWebSocket() || { isLoadingHistory: false };
const showLoadingSpinner = (isLoadingMessages && !isV1Conversation && !isTask) ||
                           (isV1Conversation && isV1LoadingHistory);

{showLoadingSpinner && (
  <div className="flex justify-center">
    <LoadingSpinner size="small" />
  </div>
)}
```

---

## Implementation Safeguards

### Hybrid Approach (Recommended)
Combine count-based detection with a timeout safety net:

```typescript
// Add debounce timer as backup
const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

// In handleMessage:
if (isLoadingHistory) {
  // Clear existing timer
  if (debounceTimerRef.current) {
    clearTimeout(debounceTimerRef.current);
  }

  // Set safety net: mark as loaded after 500ms of silence
  debounceTimerRef.current = setTimeout(() => {
    if (isLoadingHistory) {
      setIsLoadingHistory(false);
    }
  }, 500);
}

// Cleanup
return () => {
  if (debounceTimerRef.current) {
    clearTimeout(debounceTimerRef.current);
  }
};
```

---

## Pros & Cons

### Pros
✅ **Accurate** - Knows exactly when all history has been loaded
✅ **No timing dependencies** - No arbitrary debounce delays
✅ **Progress tracking** - Can show "Loading 42/150 events" progress
✅ **Testable** - Deterministic behavior, easy to test
✅ **Clean UX** - No flickering or false positives
✅ **Semantic** - Based on actual data, not heuristics

### Cons
⚠️ **Extra HTTP request** - Adds one API call on connection open
⚠️ **Slight latency** - Must wait for count response before knowing completion
⚠️ **Race condition risk** - New events could arrive between count fetch and history replay (unlikely)
⚠️ **Stale count** - If events are added during replay, count could be wrong (edge case)

---

## Alternatives Considered

1. **Debounce-only approach** (300-500ms timeout)
   - Simpler but unreliable on slow networks
   - Risk of false positives

2. **Backend enhancement** (send completion marker)
   - Most reliable but requires backend changes
   - Not currently available

3. **Event ID tracking**
   - Track highest event ID from count response
   - More complex, similar reliability to count-based

---

## Next Steps

1. ✅ **Tests created** - 3 failing tests ready
2. ⏳ **Awaiting approval** - Review implementation plan
3. ⏳ **Implement** - Add code changes per plan above
4. ⏳ **Verify** - Run tests to confirm they pass
5. ⏳ **Manual testing** - Test with real conversations

---

## Files to Modify

1. `/Users/stephan/Desktop/aha/OpenHands/frontend/src/api/conversation-service/v1-conversation-service.api.ts` - Add `getEventCount` method
2. `/Users/stephan/Desktop/aha/OpenHands/frontend/src/contexts/conversation-websocket-context.tsx` - Add loading state logic
3. `/Users/stephan/Desktop/aha/OpenHands/frontend/src/components/features/chat/chat-interface.tsx` (Optional) - Use new loading state

## Test File
- `/Users/stephan/Desktop/aha/OpenHands/frontend/__tests__/conversation-websocket-handler.test.tsx:420-580`
