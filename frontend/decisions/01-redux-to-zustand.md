# Migrate from Redux to Zustand

## Context

There are a few benefits over Redux that I think we should move to Zustand for. [To quote the official docs](https://github.com/pmndrs/zustand?tab=readme-ov-file#why-zustand-over-redux):

### Why zustand over redux?

- Simple and un-opinionated
- Makes hooks the primary means of consuming state
- Doesn't wrap your app in context providers
- [Can inform components transiently (without causing render)](https://github.com/pmndrs/zustand?tab=readme-ov-file#transient-updates-for-often-occurring-state-changes)

### Why zustand over context?

- Less boilerplate
- Renders components only on changes
- Centralized, action-based state management

Additional benefits include:

- First-class TypeScript support with zero configuration
- Improved testability:
  - No custom test renderer required
  - Simplified state manipulation
  - Direct store testing capabilities
- Middleware ecosystem, including [Persist Middleware](https://github.com/pmndrs/zustand/blob/main/docs/integrations/persisting-store-data.md) for local storage integration
- Overall enhanced developer experience with simpler API and intuitive patterns
- [Async actions](https://github.com/pmndrs/zustand?tab=readme-ov-file#async-actions)

## Decision

- Audit existing Redux stores and identify those that can be eliminated or simplified
- Apply Zustand's recommended slices pattern for multiple stores
- (?) Leverage persist middleware for session management to cache events for faster session restoration (Note: This may require modifications to the Direct Event Processing proposal)
