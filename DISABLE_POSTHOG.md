# Disabling PostHog Analytics in Production

PostHog analytics can be completely disabled in OpenHands by setting an environment variable.

## How to Disable PostHog

Set the `DISABLE_POSTHOG` environment variable to `true`:

```bash
export DISABLE_POSTHOG=true
```

Or when running with Docker:

```bash
docker run -e DISABLE_POSTHOG=true ...
```

## What This Does

When `DISABLE_POSTHOG=true` is set:

1. **Server-side**: The PostHog client key is set to an empty string in the server configuration
2. **Frontend**: The frontend receives an empty client key and automatically creates a mock PostHog object with no-op methods
3. **Analytics**: All PostHog tracking calls become no-ops, effectively disabling all analytics
4. **Error Handling**: All PostHog error tracking is disabled
5. **User Identification**: PostHog user identification is disabled

## Verification

To verify PostHog is disabled, check the server logs. You should see:
- No PostHog initialization messages
- Frontend logs showing "PostHog disabled" or similar messages

## Default Behavior

By default (when `DISABLE_POSTHOG` is not set or set to `false`), PostHog analytics remain enabled in production environments.

## Implementation Details

The implementation is located in:
- `openhands/server/config/server_config.py` - Server-side configuration
- `frontend/src/entry.client.tsx` - Frontend initialization (already handles missing keys gracefully)

This approach ensures that PostHog is completely disabled without requiring extensive code changes throughout the application.